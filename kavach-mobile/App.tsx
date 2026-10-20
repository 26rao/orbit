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
  const [inputText, setInputText] = useState('');
  const [selectedFile, setSelectedFile] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [sound, setSound] = useState<Audio.Sound | null>(null);
  const [preferredLanguage, setPreferredLanguage] = useState<'hi' | 'en' | 'te' | 'kn' | 'ta' | 'mr'>('hi');
  const [showDossierModal, setShowDossierModal] = useState(false);
  const [showFreezeModal, setShowFreezeModal] = useState(false);

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

  const playVoiceExplanation = async () => {
    if (!result?.audio_base64) {
      Alert.alert('Audio Unavailable', 'No voice memo was generated for this finding.');
      return;
    }
    try {
      if (sound) {
        await sound.unloadAsync();
      }
      const { sound: newSound } = await Audio.Sound.createAsync(
        { uri: `data:audio/mp3;base64,${result.audio_base64}` },
        { shouldPlay: true }
      );
      setSound(newSound);
    } catch (e) {
      Alert.alert('Audio Playback Error', 'Could not play voice memo.');
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

  const downloadPdf = async () => {
    if (!result?.dossier) return;
    if (Platform.OS === 'web') {
      try {
        const resp = await fetch(`${BACKEND_URL}/api/v1/dossier/pdf`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(result.dossier),
        });
        const blob = await resp.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `KavachAI_Dossier_${result.dossier.dossier_id || 'Incident'}.pdf`;
        a.click();
      } catch (err: any) {
        Alert.alert('Download Error', err.message);
      }
    } else {
      Alert.alert('Section 63 BSA PDF', 'PDF Dossier generated. Use the web dashboard or 1930 copy feature for full digital export.');
    }
  };

  const dial1930 = () => {
    Linking.openURL('tel:1930').catch(() => {
      Alert.alert('Helpline', 'Dial 1930 directly on your phone dialer.');
    });
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={{ paddingBottom: 60 }}>
      <Text style={styles.header}>KAVACH AI</Text>
      <Text style={styles.subHeader}>Universal Scam & Legal Fraud Verifier</Text>

      {/* Quick Golden Hour Trigger */}
      <TouchableOpacity style={styles.emergencyBanner} onPress={() => setShowFreezeModal(true)}>
        <Text style={styles.emergencyBannerText}>🚨 Transferred money? 1-Click Bank Account Freeze Guide</Text>
      </TouchableOpacity>

      {/* Universal Input Area */}
      <View style={styles.card}>
        <TextInput
          style={styles.textInput}
          multiline
          numberOfLines={4}
          placeholder="Paste message, payment link, UPI ID, or phone number here..."
          placeholderTextColor="#6e7681"
          value={inputText}
          onChangeText={setInputText}
        />

        <TouchableOpacity style={styles.mediaButton} onPress={pickImage}>
          <Text style={styles.mediaButtonText}>
            {selectedFile ? '✓ Document / Media Attached' : '📁 Attach Notice / QR / APK / Audio'}
          </Text>
        </TouchableOpacity>

        {/* Regional Language selector */}
        <Text style={styles.langHeader}>Select Regional Audio Voice:</Text>
        <View style={styles.langRow}>
          {[
            { code: 'hi', label: 'हिंदी' },
            { code: 'en', label: 'English' },
            { code: 'te', label: 'తెలుగు' },
            { code: 'kn', label: 'ಕನ್ನಡ' },
            { code: 'ta', label: 'தமிழ்' },
            { code: 'mr', label: 'मराठी' },
          ].map((item) => (
            <TouchableOpacity
              key={item.code}
              style={[styles.langChip, preferredLanguage === item.code && styles.langChipActive]}
              onPress={() => setPreferredLanguage(item.code as any)}
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

      {/* Forensic Verdict Screen */}
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
                ? { color: '#ff7b72' }
                : result.verdict === 'SUSPICIOUS'
                ? { color: '#e3b341' }
                : { color: '#56d364' },
            ]}
          >
            {result.verdict === 'DANGEROUS_SCAM'
              ? '🚨 FAKE & FRAUDULENT'
              : result.verdict === 'SUSPICIOUS'
              ? '⚠️ SUSPICIOUS ACTIVITY'
              : '✅ AUTHENTIC / LOW RISK'}
          </Text>
          <Text style={styles.confidence}>Confidence: {(result.confidence * 100).toFixed(0)}% · Pipeline: {result.input_modality}</Text>
          <Text style={styles.summary}>{result.summary}</Text>

          <View style={styles.reasonsList}>
            {result.reasons.map((r: string, idx: number) => (
              <Text key={idx} style={styles.reasonText}>
                • {r}
              </Text>
            ))}
          </View>

          {/* Voice Memo Button */}
          <TouchableOpacity style={styles.audioButton} onPress={playVoiceExplanation}>
            <Text style={styles.audioButtonText}>🔊 Play Regional Audio Warning</Text>
          </TouchableOpacity>

          {/* PDF Export Button */}
          {result.dossier && (
            <TouchableOpacity style={styles.pdfButton} onPress={downloadPdf}>
              <Text style={styles.pdfButtonText}>📄 Download Section 63 BSA PDF Dossier</Text>
            </TouchableOpacity>
          )}

          {/* Cybercrime Dossier Button */}
          {result.dossier && (
            <TouchableOpacity style={styles.dossierButton} onPress={() => setShowDossierModal(true)}>
              <Text style={styles.dossierButtonText}>📋 View 1930 Cybercrime Dossier</Text>
            </TouchableOpacity>
          )}

          {/* Emergency Freeze Trigger */}
          <TouchableOpacity style={styles.freezeButton} onPress={() => setShowFreezeModal(true)}>
            <Text style={styles.freezeButtonText}>⚡ Golden Hour Bank Account Freeze Guide</Text>
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
            <Text style={[styles.modalTitle, { color: '#ff7b72' }]}>🚨 Golden Hour Bank Account Freeze</Text>
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
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#0d1117', padding: 20 },
  header: { fontSize: 32, fontWeight: '900', color: '#58a6ff', textAlign: 'center', marginTop: 40 },
  subHeader: { fontSize: 14, color: '#8b949e', textAlign: 'center', marginBottom: 25 },
  card: { backgroundColor: '#161b22', padding: 16, borderRadius: 12, borderWidth: 1, borderColor: '#30363d' },
  textInput: {
    backgroundColor: '#0d1117',
    color: '#c9d1d9',
    borderRadius: 8,
    padding: 12,
    textAlignVertical: 'top',
    minHeight: 90,
  },
  mediaButton: { backgroundColor: '#21262d', padding: 12, borderRadius: 8, marginTop: 12, alignItems: 'center' },
  mediaButtonText: { color: '#58a6ff', fontWeight: '600' },
  langRow: { flexDirection: 'row', alignItems: 'center', marginTop: 14, gap: 8 },
  langLabel: { color: '#8b949e', fontSize: 13, marginRight: 4 },
  langChip: { paddingVertical: 6, paddingHorizontal: 12, borderRadius: 6, backgroundColor: '#21262d' },
  langChipActive: { backgroundColor: '#1f6feb' },
  langText: { color: '#8b949e', fontSize: 13, fontWeight: '600' },
  langTextActive: { color: '#ffffff' },
  verifyButton: { backgroundColor: '#238636', padding: 15, borderRadius: 8, marginTop: 15, alignItems: 'center' },
  verifyText: { color: '#fff', fontWeight: 'bold', fontSize: 16 },
  resultCard: { marginTop: 25, padding: 18, borderRadius: 12 },
  danger: { backgroundColor: '#3d1214', borderColor: '#f85149', borderWidth: 1 },
  warning: { backgroundColor: '#3a2707', borderColor: '#d29922', borderWidth: 1 },
  authentic: { backgroundColor: '#0d2818', borderColor: '#238636', borderWidth: 1 },
  verdictTitle: { fontSize: 20, fontWeight: '800', marginBottom: 4 },
  confidence: { fontSize: 13, color: '#8b949e', marginBottom: 10 },
  summary: { fontSize: 15, fontWeight: '600', color: '#fff', marginBottom: 12 },
  reasonsList: { marginVertical: 8 },
  reasonText: { color: '#c9d1d9', fontSize: 14, lineHeight: 20, marginBottom: 6 },
  audioButton: { backgroundColor: '#1f6feb', padding: 12, borderRadius: 8, alignItems: 'center', marginTop: 12 },
  audioButtonText: { color: '#fff', fontWeight: '700' },
  dossierButton: { backgroundColor: '#30363d', padding: 12, borderRadius: 8, alignItems: 'center', marginTop: 10 },
  dossierButtonText: { color: '#c9d1d9', fontWeight: '700' },
  modalBackdrop: { flex: 1, backgroundColor: 'rgba(0,0,0,0.85)', justifyContent: 'center', padding: 20 },
  modalContent: { backgroundColor: '#161b22', borderRadius: 12, padding: 20, maxHeight: '80%' },
  modalTitle: { fontSize: 18, fontWeight: '800', color: '#58a6ff', marginBottom: 12 },
  dossierScroll: { maxHeight: 350, backgroundColor: '#0d1117', padding: 12, borderRadius: 8 },
  dossierCode: { color: '#8b949e', fontFamily: 'monospace', fontSize: 12 },
  modalButtons: { flexDirection: 'row', justifyContent: 'flex-end', marginTop: 16, gap: 10 },
  shareButton: { backgroundColor: '#238636', paddingVertical: 8, paddingHorizontal: 16, borderRadius: 6 },
  shareText: { color: '#fff', fontWeight: '700' },
  closeButton: { backgroundColor: '#30363d', paddingVertical: 8, paddingHorizontal: 16, borderRadius: 6 },
  closeText: { color: '#c9d1d9', fontWeight: '700' },
  emergencyBanner: {
    backgroundColor: '#3d1214',
    borderColor: '#f85149',
    borderWidth: 1,
    padding: 10,
    borderRadius: 8,
    marginBottom: 16,
    alignItems: 'center',
  },
  emergencyBannerText: { color: '#ff7b72', fontWeight: '700', fontSize: 13 },
  langHeader: { color: '#8b949e', fontSize: 13, marginTop: 14, marginBottom: 6, fontWeight: '600' },
  pdfButton: { backgroundColor: '#238636', padding: 12, borderRadius: 8, alignItems: 'center', marginTop: 10 },
  pdfButtonText: { color: '#fff', fontWeight: '700' },
  freezeButton: { backgroundColor: '#4c1d24', borderWidth: 1, borderColor: '#f85149', padding: 12, borderRadius: 8, alignItems: 'center', marginTop: 10 },
  freezeButtonText: { color: '#ff7b72', fontWeight: '700' },
  freezeDesc: { color: '#c9d1d9', fontSize: 13, lineHeight: 18, marginBottom: 12 },
  dialBtn: { backgroundColor: '#dc2626', padding: 10, borderRadius: 8, alignItems: 'center', marginBottom: 14 },
  dialBtnText: { color: '#fff', fontWeight: '700', fontSize: 14 },
  bankHeader: { color: '#58a6ff', fontWeight: '700', fontSize: 13, marginBottom: 6 },
  bankItem: { color: '#8b949e', fontSize: 12, lineHeight: 18, marginBottom: 4 },
});
