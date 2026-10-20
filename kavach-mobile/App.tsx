import React, { useState } from 'react';
import {
  StyleSheet,
  Text,
  View,
  TextInput,
  TouchableOpacity,
  ScrollView,
  ActivityIndicator,
  Alert,
  Modal,
  Share,
  Platform,
  Linking,
} from 'react-native';
import * as ImagePicker from 'expo-image-picker';
import { Audio } from 'expo-av';

const BACKEND_URL = Platform.OS === 'android' ? 'http://10.0.2.2:8000' : 'http://localhost:8000';

export default function App() {
  const [activeTab, setActiveTab] = useState<'message' | 'document' | 'payment' | 'url'>('message');
  const [inputText, setInputText] = useState('');
  const [selectedFile, setSelectedFile] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [sound, setSound] = useState<Audio.Sound | null>(null);
  const [isPlayingAudio, setIsPlayingAudio] = useState(false);
  const [preferredLanguage, setPreferredLanguage] = useState<'hi' | 'en' | 'te' | 'kn' | 'ta' | 'mr'>('hi');
  const [showDossierModal, setShowDossierModal] = useState(false);
  const [showFreezeModal, setShowFreezeModal] = useState(false);
  const [openAccordion, setOpenAccordion] = useState<string | null>('legal');

  const pickImage = async () => {
    try {
      const res = await ImagePicker.launchImageLibraryAsync({
        mediaTypes: ImagePicker.MediaTypeOptions.All,
        allowsEditing: false,
        quality: 1,
      });
      if (!res.canceled && res.assets && res.assets.length > 0) {
        setSelectedFile(res.assets[0]);
      }
    } catch (e) {
      Alert.alert('File Picker', 'Unable to access device media library.');
    }
  };

  const handleVerify = async () => {
    if (!inputText && !selectedFile) {
      Alert.alert('Input needed', 'Please paste text/link or choose a file to verify.');
      return;
    }

    setLoading(true);
    setResult(null);
    if (sound) {
      await sound.unloadAsync();
      setSound(null);
      setIsPlayingAudio(false);
    }

    try {
      const formData = new FormData();
      if (inputText) formData.append('text_content', inputText);
      if (selectedFile) {
        if (Platform.OS === 'web') {
          const resBlob = await fetch(selectedFile.uri);
          const blob = await resBlob.blob();
          formData.append('file', blob, selectedFile.fileName || 'upload.jpg');
        } else {
          formData.append('file', {
            uri: selectedFile.uri,
            name: selectedFile.fileName || 'upload.jpg',
            type: selectedFile.mimeType || 'image/jpeg',
          } as any);
        }
      }
      formData.append('preferred_language', preferredLanguage);

      const response = await fetch(`${BACKEND_URL}/api/v1/verify`, {
        method: 'POST',
        body: formData,
      });
      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Server returned ${response.status}: ${errorText}`);
      }
      const data = await response.json();
      setResult(data);
    } catch (e: any) {
      Alert.alert('Forensic Verification Error', e.message || 'Could not complete forensic verification.');
    } finally {
      setLoading(false);
    }
  };

  // Fixed Play/Pause toggle that reliably pauses and resumes
  const toggleVoicePlayback = async () => {
    if (!result?.audio_base64) {
      Alert.alert('Audio Unavailable', 'No voice memo is available for this finding.');
      return;
    }

    try {
      if (sound) {
        const status = await sound.getStatusAsync();
        if (status.isLoaded) {
          if (status.isPlaying) {
            await sound.pauseAsync();
            setIsPlayingAudio(false);
            return;
          } else {
            await sound.playAsync();
            setIsPlayingAudio(true);
            return;
          }
        }
      }

      // Create new sound instance
      const { sound: newSound } = await Audio.Sound.createAsync(
        { uri: `data:audio/mp3;base64,${result.audio_base64}` },
        { shouldPlay: true }
      );
      setSound(newSound);
      setIsPlayingAudio(true);

      newSound.setOnPlaybackStatusUpdate((status) => {
        if (!status.isLoaded || status.didJustFinish) {
          setIsPlayingAudio(false);
        }
      });
    } catch (e) {
      console.log('Audio error:', e);
      Alert.alert('Audio Playback', 'Could not toggle voice memo.');
      setIsPlayingAudio(false);
    }
  };

  const shareDossier = async () => {
    if (!result?.dossier?.fir_narrative_template) return;
    try {
      await Share.share({
        message: result.dossier.fir_narrative_template,
        title: 'National Cybercrime Portal Complaint Form 1930',
      });
    } catch (e) {
      console.log('Share error:', e);
    }
  };

  const shareWarningWithFamily = async () => {
    const headline = getHeroHeadline();
    const shareText = `⚠️ CYBERCRIME ALERT: ${headline}\n\nDo NOT transfer money or share UPI PINs. If someone contacted you claiming to be police/CBI, report immediately to Helpline 1930.\n\nVerified by KavachAI.`;
    try {
      await Share.share({
        message: shareText,
        title: 'Cybercrime Warning',
      });
    } catch (e) {
      console.log('Share error:', e);
    }
  };

  const downloadPdf = async () => {
    if (!result?.dossier) return;
    if (Platform.OS === 'web') {
      try {
        const resp = await fetch(`${BACKEND_URL}/api/v1/dossier/pdf`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(result.dossier),
        });
        if (!resp.ok) {
          throw new Error('Server PDF route not ready. Falling back to digital copy.');
        }
        const blob = await resp.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `KavachAI_Dossier_${result.dossier.dossier_id || 'Incident'}.pdf`;
        a.click();
      } catch (err: any) {
        Alert.alert('PDF Export Notice', err.message);
        shareDossier();
      }
    } else {
      shareDossier();
    }
  };

  const changeLanguage = async (newLang: any) => {
    setPreferredLanguage(newLang);
    if (sound) {
      await sound.unloadAsync();
      setSound(null);
      setIsPlayingAudio(false);
    }

    if (result) {
      try {
        const resp = await fetch(`${BACKEND_URL}/api/v1/voice-memo`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            reasons: result.reasons || [],
            preferred_language: newLang,
            verdict: result.verdict || 'DANGEROUS_SCAM',
          }),
        });
        if (resp.ok) {
          const data = await resp.json();
          setResult({ ...result, audio_base64: data.audio_base64 });
        }
      } catch (e) {
        console.log('Language audio update error:', e);
      }
    }
  };

  const dial1930 = () => {
    Linking.openURL('tel:1930').catch(() => {
      Alert.alert('Helpline', 'Dial 1930 directly on your phone dialer.');
    });
  };

  const getHeroHeadline = () => {
    if (!result) return '';
    const text = (result.summary + ' ' + (result.reasons || []).join(' ')).toLowerCase();
    if (text.includes('cbi') || text.includes('arrest') || text.includes('police')) {
      return 'This CBI notice is 100% fake. Police in India do not arrest people over WhatsApp video calls.';
    } else if (text.includes('electricity') || text.includes('power') || text.includes('apk')) {
      return 'This electricity power-cut notice is a phishing scam. Electricity boards never ask citizens to install .apk files.';
    } else if (text.includes('upi') || text.includes('refund') || text.includes('collect')) {
      return 'This collect request will deduct money from your account. You NEVER enter a UPI PIN to receive money.';
    } else if (text.includes('sebi') || text.includes('trading') || text.includes('stock')) {
      return 'This WhatsApp/Telegram stock tips group is an unregistered illegal boiler room scam.';
    }
    return result.summary || 'Critical Fraud Detected. Do not transfer funds.';
  };

  const isScam = result?.verdict === 'DANGEROUS_SCAM';

  return (
    <View style={{ flex: 1, backgroundColor: '#060911' }}>
      {/* 1. Dynamic Threat Level Banner */}
      {isScam && (
        <View style={styles.topThreatAlert}>
          <Text style={styles.topThreatAlertText}>
            🚨 DO NOT TRANSFER FUNDS • DO NOT ENTER UPI PIN
          </Text>
        </View>
      )}

      <ScrollView style={styles.container} contentContainerStyle={{ paddingBottom: 120 }}>
        <Text style={styles.header}>KAVACH AI</Text>
        <Text style={styles.subHeader}>National Cybercrime Forensics & Legal Defense Console</Text>

        {/* 1. TOP ANCHORED EMERGENCY FREEZE BANNER BUTTON */}
        <TouchableOpacity style={styles.emergencyBanner} onPress={() => setShowFreezeModal(true)}>
          <Text style={styles.emergencyBannerText}>🚨 Transferred money? 1-Click Bank Account Freeze Guide</Text>
        </TouchableOpacity>

        {/* 2. TABBED / PILL MODE SWITCHER */}
        <View style={styles.modeTabBar}>
          <TouchableOpacity
            style={[styles.modeTab, activeTab === 'message' && styles.modeTabActive]}
            onPress={() => setActiveTab('message')}
          >
            <Text style={[styles.modeTabText, activeTab === 'message' && styles.modeTabTextActive]}>💬 Text</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.modeTab, activeTab === 'document' && styles.modeTabActive]}
            onPress={() => setActiveTab('document')}
          >
            <Text style={[styles.modeTabText, activeTab === 'document' && styles.modeTabTextActive]}>📄 Notice PDF</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.modeTab, activeTab === 'payment' && styles.modeTabActive]}
            onPress={() => setActiveTab('payment')}
          >
            <Text style={[styles.modeTabText, activeTab === 'payment' && styles.modeTabTextActive]}>💳 QR / UPI</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.modeTab, activeTab === 'url' && styles.modeTabActive]}
            onPress={() => setActiveTab('url')}
          >
            <Text style={[styles.modeTabText, activeTab === 'url' && styles.modeTabTextActive]}>🔗 Link / APK</Text>
          </TouchableOpacity>
        </View>

        {/* Input Card */}
        <View style={styles.card}>
          {activeTab === 'message' && (
            <TextInput
              style={styles.textInput}
              multiline
              numberOfLines={4}
              placeholder="Paste suspicious SMS, WhatsApp message, Telegram stock tip..."
              placeholderTextColor="#64748b"
              value={inputText}
              onChangeText={setInputText}
            />
          )}

          {activeTab === 'document' && (
            <TouchableOpacity style={styles.dropzoneCard} onPress={pickImage}>
              <Text style={{ fontSize: 30, marginBottom: 6 }}>📑</Text>
              <Text style={{ color: '#fff', fontWeight: '700', fontSize: 14 }}>
                {selectedFile ? '✓ Notice Document Attached' : 'Attach Court Notice or Warrant PDF / Image'}
              </Text>
              <Text style={{ color: '#64748b', fontSize: 12, marginTop: 4 }}>
                Extracts fake judicial seals & forged CNR numbers
              </Text>
            </TouchableOpacity>
          )}

          {activeTab === 'payment' && (
            <View>
              <TouchableOpacity style={styles.dropzoneCard} onPress={pickImage}>
                <Text style={{ fontSize: 26, marginBottom: 4 }}>📷</Text>
                <Text style={{ color: '#fff', fontWeight: '700', fontSize: 14 }}>
                  {selectedFile ? '✓ QR Image Attached' : 'Attach UPI QR Code Image'}
                </Text>
              </TouchableOpacity>
              <TextInput
                style={[styles.textInput, { marginTop: 10, minHeight: 45 }]}
                placeholder="Or paste UPI handle (e.g. refund@oksbi)"
                placeholderTextColor="#64748b"
                value={inputText}
                onChangeText={setInputText}
              />
            </View>
          )}

          {activeTab === 'url' && (
            <View>
              <TextInput
                style={[styles.textInput, { minHeight: 45 }]}
                placeholder="Paste URL (e.g. https://bijli-bill-update.online/app.apk)"
                placeholderTextColor="#64748b"
                value={inputText}
                onChangeText={setInputText}
              />
              <TouchableOpacity style={[styles.mediaButton, { marginTop: 10 }]} onPress={pickImage}>
                <Text style={styles.mediaButtonText}>
                  {selectedFile ? '✓ APK File Attached' : '📦 Or Attach .APK File'}
                </Text>
              </TouchableOpacity>
            </View>
          )}

          {/* Pre-Verification Language Selector */}
          <Text style={styles.langHeader}>Voice Memo Language:</Text>
          <View style={styles.langRow}>
            {[
              { code: 'hi', label: 'हिंदी' },
              { code: 'en', label: 'English' },
              { code: 'kn', label: 'ಕನ್ನಡ' },
              { code: 'te', label: 'తెలుగు' },
              { code: 'ta', label: 'தமிழ்' },
              { code: 'mr', label: 'मराठी' },
            ].map((item) => (
              <TouchableOpacity
                key={item.code}
                style={[styles.langChip, preferredLanguage === item.code && styles.langChipActive]}
                onPress={() => changeLanguage(item.code as any)}
              >
                <Text style={[styles.langText, preferredLanguage === item.code && styles.langTextActive]}>
                  {item.label}
                </Text>
              </TouchableOpacity>
            ))}
          </View>

          <TouchableOpacity style={styles.verifyButton} onPress={handleVerify} disabled={loading}>
            {loading ? <ActivityIndicator color="#fff" /> : <Text style={styles.verifyText}>VERIFY NOW</Text>}
          </TouchableOpacity>
        </View>

        {/* 3. VERDICT WITH PROGRESSIVE DISCLOSURE */}
        {result && (
          <View
            style={[
              styles.resultCard,
              result.verdict === 'DANGEROUS_SCAM'
                ? styles.danger
                : result.verdict === 'SUSPICIOUS'
                ? styles.warning
                : styles.authentic,
            ]}
          >
            <Text
              style={[
                styles.verdictTitle,
                result.verdict === 'DANGEROUS_SCAM'
                  ? { color: '#ef4444' }
                  : result.verdict === 'SUSPICIOUS'
                  ? { color: '#f59e0b' }
                  : { color: '#10b981' },
              ]}
            >
              {result.verdict === 'DANGEROUS_SCAM'
                ? '🚨 CRITICAL FRAUD DETECTED'
                : result.verdict === 'SUSPICIOUS'
                ? '⚠️ SUSPICIOUS ACTIVITY'
                : '✅ AUTHENTIC / LOW RISK'}
            </Text>
            <Text style={styles.confidence}>Confidence: {(result.confidence * 100).toFixed(0)}% · Pipeline: {result.input_modality}</Text>

            {/* Level 1: Human Takeaway (Hero Card) */}
            <View style={styles.heroTakeaway}>
              <Text style={styles.heroTakeawayTitle}>{getHeroHeadline()}</Text>
              <Text style={styles.heroTakeawaySub}>
                {result.verdict === 'DANGEROUS_SCAM'
                  ? 'Do not panic. Under Indian law (BNSS 2023), digital arrests are non-existent. Do not transfer funds.'
                  : result.summary}
              </Text>
            </View>

            {/* 4. WhatsApp-Style Voice Note Widget with pause toggle */}
            <View style={styles.voiceNotePlayer}>
              <TouchableOpacity style={styles.voicePlayBtn} onPress={toggleVoicePlayback}>
                <Text style={{ color: '#fff', fontSize: 15, fontWeight: 'bold' }}>
                  {isPlayingAudio ? '❚❚' : '▶'}
                </Text>
              </TouchableOpacity>
              <View style={styles.waveformRow}>
                {[10, 16, 22, 12, 18, 24, 14, 20, 12, 16, 24, 18, 12].map((h, i) => (
                  <View
                    key={i}
                    style={[
                      styles.waveformBar,
                      { height: isPlayingAudio ? (i % 2 === 0 ? 22 : 10) : h },
                    ]}
                  />
                ))}
              </View>
              <Text style={styles.voiceTimer}>{isPlayingAudio ? 'Playing' : '0:14'}</Text>
            </View>

            {/* Language Switcher Pills */}
            <View style={styles.langPillsRow}>
              {[
                { code: 'hi', label: 'हिन्दी' },
                { code: 'en', label: 'EN' },
                { code: 'kn', label: 'ಕನ್ನಡ' },
                { code: 'te', label: 'తెలుగు' },
                { code: 'ta', label: 'தமிழ்' },
                { code: 'mr', label: 'मराठी' },
              ].map((item) => (
                <TouchableOpacity
                  key={item.code}
                  style={[styles.pillBtn, preferredLanguage === item.code && styles.pillBtnActive]}
                  onPress={() => changeLanguage(item.code as any)}
                >
                  <Text style={[styles.pillBtnText, preferredLanguage === item.code && styles.pillBtnTextActive]}>
                    {item.label}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>

            {/* Level 2: Interactive Accordions */}
            <Text style={styles.breakdownHeader}>FORENSIC BREAKDOWN</Text>

            <TouchableOpacity
              style={styles.accordionHeader}
              onPress={() => setOpenAccordion(openAccordion === 'legal' ? null : 'legal')}
            >
              <Text style={styles.accordionTitle}>🏛️ Legal Verification</Text>
              <Text style={{ color: '#94a3b8' }}>{openAccordion === 'legal' ? '▲' : '▼'}</Text>
            </TouchableOpacity>
            {openAccordion === 'legal' && (
              <View style={styles.accordionBody}>
                <Text style={styles.accordionBodyText}>
                  {result.reasons?.filter((r: string) => r.toLowerCase().includes('court') || r.toLowerCase().includes('arrest') || r.toLowerCase().includes('cbi') || r.toLowerCase().includes('law')).join('\n• ') || '• Legal procedural check complete.'}
                </Text>
              </View>
            )}

            <TouchableOpacity
              style={styles.accordionHeader}
              onPress={() => setOpenAccordion(openAccordion === 'payment' ? null : 'payment')}
            >
              <Text style={styles.accordionTitle}>💳 Payment & Cyber Infrastructure</Text>
              <Text style={{ color: '#94a3b8' }}>{openAccordion === 'payment' ? '▲' : '▼'}</Text>
            </TouchableOpacity>
            {openAccordion === 'payment' && (
              <View style={styles.accordionBody}>
                <Text style={styles.accordionBodyText}>
                  {result.reasons?.filter((r: string) => r.toLowerCase().includes('upi') || r.toLowerCase().includes('payment') || r.toLowerCase().includes('vpa')).join('\n• ') || '• Payment channel check complete.'}
                </Text>
              </View>
            )}

            <TouchableOpacity
              style={styles.accordionHeader}
              onPress={() => setOpenAccordion(openAccordion === 'domain' ? null : 'domain')}
            >
              <Text style={styles.accordionTitle}>🌐 Threat Intel & Domain Verification</Text>
              <Text style={{ color: '#94a3b8' }}>{openAccordion === 'domain' ? '▲' : '▼'}</Text>
            </TouchableOpacity>
            {openAccordion === 'domain' && (
              <View style={styles.accordionBody}>
                <Text style={styles.accordionBodyText}>
                  {result.reasons?.filter((r: string) => r.toLowerCase().includes('domain') || r.toLowerCase().includes('apk') || r.toLowerCase().includes('sms')).join('\n• ') || '• Domain infrastructure scan complete.'}
                </Text>
              </View>
            )}

            {/* Level 3: Forensic Details Drawer */}
            <TouchableOpacity
              style={[styles.accordionHeader, { marginTop: 12, borderColor: '#334155' }]}
              onPress={() => setOpenAccordion(openAccordion === 'forensic' ? null : 'forensic')}
            >
              <Text style={[styles.accordionTitle, { fontSize: 13, color: '#94a3b8' }]}>
                🔍 Forensic Hashes & Citations (BSA 2023)
              </Text>
              <Text style={{ color: '#94a3b8' }}>{openAccordion === 'forensic' ? '▲' : '▼'}</Text>
            </TouchableOpacity>
            {openAccordion === 'forensic' && (
              <View style={styles.accordionBody}>
                <Text style={styles.monoText}>
                  Dossier ID: {result.dossier?.dossier_id || 'N/A'}{'\n'}
                  Hash: SHA-256: {(result.dossier?.sha256_evidence_hash || '').slice(0, 24)}...{'\n'}
                  Statutes: {(result.dossier?.statutory_violations || []).join(', ')}
                </Text>
              </View>
            )}

            {/* Export & Action Buttons */}
            <View style={{ marginTop: 18, gap: 10 }}>
              <TouchableOpacity style={styles.pdfButton} onPress={downloadPdf}>
                <Text style={styles.pdfButtonText}>📄 Court-Admissible Section 63 BSA PDF</Text>
              </TouchableOpacity>
              <TouchableOpacity style={styles.dossierButton} onPress={() => setShowDossierModal(true)}>
                <Text style={styles.dossierButtonText}>📋 View 1930 Cybercrime Dossier</Text>
              </TouchableOpacity>
            </View>
          </View>
        )}
      </ScrollView>

      {/* 5. FLOATING EMERGENCY ACTION BOTTOM SHEET (Active when Scam Detected) */}
      {isScam && (
        <View style={styles.bottomSheet}>
          <TouchableOpacity style={styles.bottomSheetCallBtn} onPress={dial1930}>
            <Text style={styles.bottomSheetCallText}>📞 Call 1930</Text>
          </TouchableOpacity>
          <TouchableOpacity style={styles.bottomSheetSecBtn} onPress={shareDossier}>
            <Text style={styles.bottomSheetSecText}>📋 Copy Complaint</Text>
          </TouchableOpacity>
          <TouchableOpacity style={styles.bottomSheetSecBtn} onPress={shareWarningWithFamily}>
            <Text style={styles.bottomSheetSecText}>↗️ Share Alert</Text>
          </TouchableOpacity>
        </View>
      )}

      {/* Dossier Modal */}
      <Modal visible={showDossierModal} animationType="slide" transparent={true}>
        <View style={styles.modalBackdrop}>
          <View style={styles.modalContent}>
            <Text style={styles.modalTitle}>National Cybercrime Report (1930)</Text>
            <ScrollView style={styles.dossierScroll}>
              <Text style={styles.dossierCode}>
                {result?.dossier?.fir_narrative_template || JSON.stringify(result?.dossier, null, 2)}
              </Text>
            </ScrollView>
            <View style={styles.modalButtons}>
              <TouchableOpacity style={styles.shareButton} onPress={shareDossier}>
                <Text style={styles.shareText}>Share / Copy</Text>
              </TouchableOpacity>
              <TouchableOpacity style={styles.closeButton} onPress={() => setShowDossierModal(false)}>
                <Text style={styles.closeText}>Close</Text>
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>

      {/* Golden Hour Bank Freeze Modal */}
      <Modal visible={showFreezeModal} animationType="slide" transparent={true}>
        <View style={styles.modalBackdrop}>
          <View style={styles.modalContent}>
            <Text style={[styles.modalTitle, { color: '#ef4444' }]}>🚨 Golden Hour Bank Account Freeze</Text>
            <ScrollView style={styles.dossierScroll}>
              <Text style={styles.freezeDesc}>
                Transfer recall is most successful in the first 60-120 minutes. Immediately dial 1930 or execute your bank's emergency SMS lock:
              </Text>
              <TouchableOpacity style={styles.dialBtn} onPress={dial1930}>
                <Text style={styles.dialBtnText}>📞 Call 1930 Cyber Helpline</Text>
              </TouchableOpacity>
              <Text style={styles.bankHeader}>Bank Emergency Shortcodes:</Text>
              <Text style={styles.bankItem}>• SBI: SMS BLOCK XXXX to 567676 | Stop UPI: 9223008333</Text>
              <Text style={styles.bankItem}>• HDFC: SMS BLOCK XXXX to 5676712 | Call 1800 1600</Text>
              <Text style={styles.bankItem}>• ICICI: SMS BLOCK XXXX to 5676766 | Stop UPI: 9215676766</Text>
              <Text style={styles.bankItem}>• Axis: SMS BLOCK XXXX to 5676782 | Call 1860 419 5555</Text>
              <Text style={styles.bankItem}>• PNB: SMS HOT &lt;CardNo&gt; to 5607040 | Call 1800 180 2222</Text>
            </ScrollView>
            <View style={styles.modalButtons}>
              <TouchableOpacity style={styles.closeButton} onPress={() => setShowFreezeModal(false)}>
                <Text style={styles.closeText}>Close</Text>
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#060911', padding: 18 },
  topThreatAlert: {
    backgroundColor: '#b91c1c',
    paddingVertical: 10,
    paddingHorizontal: 16,
    alignItems: 'center',
    justifyContent: 'center',
  },
  topThreatAlertText: { color: '#ffffff', fontWeight: '900', fontSize: 13, letterSpacing: 0.5 },
  header: { fontSize: 26, fontWeight: '900', color: '#60a5fa', textAlign: 'center', marginTop: 15 },
  subHeader: { fontSize: 12.5, color: '#94a3b8', textAlign: 'center', marginBottom: 18 },
  emergencyBanner: {
    backgroundColor: 'rgba(239, 68, 68, 0.12)',
    borderColor: 'rgba(239, 68, 68, 0.55)',
    borderWidth: 1,
    padding: 12,
    borderRadius: 12,
    marginBottom: 16,
    alignItems: 'center',
    shadowColor: '#ef4444',
    shadowOpacity: 0.2,
    shadowRadius: 8,
  },
  emergencyBannerText: { color: '#fca5a5', fontWeight: '700', fontSize: 13 },
  modeTabBar: {
    flexDirection: 'row',
    backgroundColor: '#101828',
    borderRadius: 10,
    padding: 4,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: '#1e2e4a',
  },
  modeTab: { flex: 1, paddingVertical: 8, alignItems: 'center', borderRadius: 8 },
  modeTabActive: { backgroundColor: '#16233b', borderWidth: 1, borderColor: '#3b82f6' },
  modeTabText: { color: '#94a3b8', fontSize: 12, fontWeight: '600' },
  modeTabTextActive: { color: '#ffffff', fontWeight: '700' },
  card: { backgroundColor: '#101828', padding: 16, borderRadius: 14, borderWidth: 1, borderColor: '#1e2e4a' },
  textInput: {
    backgroundColor: '#060911',
    color: '#f8fafc',
    borderRadius: 8,
    padding: 12,
    textAlignVertical: 'top',
    minHeight: 85,
    borderWidth: 1,
    borderColor: '#1e2e4a',
    fontSize: 14,
  },
  dropzoneCard: {
    borderWidth: 2,
    borderStyle: 'dashed',
    borderColor: '#1e2e4a',
    backgroundColor: 'rgba(6, 9, 17, 0.5)',
    borderRadius: 10,
    padding: 20,
    alignItems: 'center',
  },
  mediaButton: { backgroundColor: '#16233b', padding: 10, borderRadius: 8, alignItems: 'center' },
  mediaButtonText: { color: '#60a5fa', fontWeight: '600', fontSize: 13 },
  langHeader: { color: '#94a3b8', fontSize: 12, fontWeight: '700', marginTop: 14, marginBottom: 6 },
  langRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 6, marginBottom: 6 },
  langChip: { paddingVertical: 5, paddingHorizontal: 12, borderRadius: 16, backgroundColor: '#16233b', borderWidth: 1, borderColor: '#1e2e4a' },
  langChipActive: { backgroundColor: '#2563eb', borderColor: '#3b82f6' },
  langText: { color: '#94a3b8', fontSize: 12, fontWeight: '600' },
  langTextActive: { color: '#ffffff' },
  verifyButton: { backgroundColor: '#ef4444', padding: 13, borderRadius: 10, marginTop: 14, alignItems: 'center' },
  verifyText: { color: '#fff', fontWeight: '800', fontSize: 15, letterSpacing: 0.5 },
  resultCard: { marginTop: 22, padding: 18, borderRadius: 14 },
  danger: { backgroundColor: 'rgba(60, 10, 15, 0.96)', borderColor: '#ef4444', borderWidth: 1.5 },
  warning: { backgroundColor: 'rgba(58, 39, 7, 0.96)', borderColor: '#f59e0b', borderWidth: 1.5 },
  authentic: { backgroundColor: 'rgba(10, 45, 25, 0.96)', borderColor: '#10b981', borderWidth: 1.5 },
  verdictTitle: { fontSize: 19, fontWeight: '900', marginBottom: 4 },
  confidence: { fontSize: 12.5, color: '#94a3b8', marginBottom: 12 },
  heroTakeaway: {
    backgroundColor: 'rgba(0,0,0,0.35)',
    borderLeftWidth: 4,
    borderLeftColor: '#ef4444',
    padding: 12,
    borderRadius: 8,
    marginBottom: 14,
  },
  heroTakeawayTitle: { color: '#ffffff', fontSize: 15, fontWeight: '800', lineHeight: 20, marginBottom: 4 },
  heroTakeawaySub: { color: '#cbd5e1', fontSize: 13, lineHeight: 18 },
  voiceNotePlayer: {
    backgroundColor: '#101828',
    borderWidth: 1,
    borderColor: 'rgba(59, 130, 246, 0.35)',
    borderRadius: 24,
    paddingVertical: 8,
    paddingHorizontal: 14,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    marginBottom: 10,
  },
  voicePlayBtn: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: '#2563eb',
    alignItems: 'center',
    justifyContent: 'center',
  },
  waveformRow: { flexDirection: 'row', alignItems: 'center', gap: 3, flex: 1 },
  waveformBar: { width: 3, backgroundColor: '#3b82f6', borderRadius: 2 },
  voiceTimer: { color: '#94a3b8', fontSize: 12, fontFamily: 'monospace' },
  langPillsRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 6, marginBottom: 14 },
  pillBtn: { paddingVertical: 4, paddingHorizontal: 10, borderRadius: 12, backgroundColor: '#16233b' },
  pillBtnActive: { backgroundColor: '#2563eb' },
  pillBtnText: { color: '#94a3b8', fontSize: 11.5, fontWeight: '600' },
  pillBtnTextActive: { color: '#fff' },
  breakdownHeader: { color: '#94a3b8', fontSize: 12, fontWeight: '800', letterSpacing: 0.8, marginBottom: 8 },
  accordionHeader: {
    backgroundColor: 'rgba(255,255,255,0.03)',
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.08)',
    borderRadius: 8,
    padding: 10,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 4,
  },
  accordionTitle: { color: '#fff', fontSize: 13, fontWeight: '700' },
  accordionBody: {
    backgroundColor: 'rgba(0,0,0,0.25)',
    padding: 10,
    borderRadius: 8,
    marginBottom: 8,
  },
  accordionBodyText: { color: '#cbd5e1', fontSize: 12.5, lineHeight: 18 },
  monoText: { color: '#94a3b8', fontFamily: 'monospace', fontSize: 11, lineHeight: 16 },
  pdfButton: { backgroundColor: '#059669', padding: 12, borderRadius: 8, alignItems: 'center' },
  pdfButtonText: { color: '#fff', fontWeight: '700', fontSize: 13.5 },
  dossierButton: { backgroundColor: '#16233b', padding: 12, borderRadius: 8, alignItems: 'center', borderWidth: 1, borderColor: '#1e2e4a' },
  dossierButtonText: { color: '#e2e8f0', fontWeight: '700', fontSize: 13.5 },
  bottomSheet: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    backgroundColor: '#0c121e',
    borderTopWidth: 2,
    borderTopColor: '#ef4444',
    paddingVertical: 12,
    paddingHorizontal: 16,
    flexDirection: 'row',
    justifyContent: 'space-between',
    gap: 8,
  },
  bottomSheetCallBtn: {
    flex: 1.2,
    backgroundColor: '#dc2626',
    borderRadius: 8,
    paddingVertical: 10,
    alignItems: 'center',
    justifyContent: 'center',
  },
  bottomSheetCallText: { color: '#fff', fontWeight: '800', fontSize: 13 },
  bottomSheetSecBtn: {
    flex: 1,
    backgroundColor: '#16233b',
    borderWidth: 1,
    borderColor: '#1e2e4a',
    borderRadius: 8,
    paddingVertical: 10,
    alignItems: 'center',
    justifyContent: 'center',
  },
  bottomSheetSecText: { color: '#f8fafc', fontWeight: '600', fontSize: 12 },
  modalBackdrop: { flex: 1, backgroundColor: 'rgba(0,0,0,0.85)', justifyContent: 'center', padding: 18 },
  modalContent: { backgroundColor: '#101828', borderRadius: 14, padding: 18, maxHeight: '82%', borderWidth: 1, borderColor: '#1e2e4a' },
  modalTitle: { fontSize: 17, fontWeight: '800', color: '#60a5fa', marginBottom: 10 },
  dossierScroll: { maxHeight: 340, backgroundColor: '#060911', padding: 12, borderRadius: 8 },
  dossierCode: { color: '#cbd5e1', fontFamily: 'monospace', fontSize: 11.5, lineHeight: 16 },
  modalButtons: { flexDirection: 'row', justifyContent: 'flex-end', marginTop: 14, gap: 10 },
  shareButton: { backgroundColor: '#059669', paddingVertical: 8, paddingHorizontal: 14, borderRadius: 6 },
  shareText: { color: '#fff', fontWeight: '700', fontSize: 13 },
  closeButton: { backgroundColor: '#16233b', paddingVertical: 8, paddingHorizontal: 14, borderRadius: 6 },
  closeText: { color: '#cbd5e1', fontWeight: '700', fontSize: 13 },
  freezeDesc: { color: '#cbd5e1', fontSize: 13, lineHeight: 18, marginBottom: 12 },
  dialBtn: { backgroundColor: '#dc2626', padding: 10, borderRadius: 8, alignItems: 'center', marginBottom: 12 },
  dialBtnText: { color: '#fff', fontWeight: '700', fontSize: 14 },
  bankHeader: { color: '#60a5fa', fontWeight: '700', fontSize: 13, marginBottom: 6 },
  bankItem: { color: '#94a3b8', fontSize: 12, lineHeight: 18, marginBottom: 4 },
});
