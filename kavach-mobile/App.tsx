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
} from 'react-native';
import * as ImagePicker from 'expo-image-picker';
import { Audio } from 'expo-av';

const BACKEND_URL = 'http://10.0.2.2:8000'; // Change to production IP or 10.0.2.2 for Android emulator

export default function App() {
  const [inputText, setInputText] = useState('');
  const [selectedFile, setSelectedFile] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [sound, setSound] = useState<Audio.Sound | null>(null);
  const [preferredLanguage, setPreferredLanguage] = useState<'hi' | 'en'>('hi');
  const [showDossierModal, setShowDossierModal] = useState(false);

  const pickImage = async () => {
    try {
      const res = await ImagePicker.launchImageLibraryAsync({
        mediaTypes: ImagePicker.MediaTypeOptions.Images,
        allowsEditing: false,
        quality: 1,
      });
      if (!res.canceled && res.assets && res.assets.length > 0) {
        setSelectedFile(res.assets[0]);
      }
    } catch (e) {
      Alert.alert('File Picker', 'Unable to access device image library.');
    }
  };

  const handleVerify = async () => {
    if (!inputText && !selectedFile) {
      Alert.alert('Input needed', 'Please paste text/link or choose an image to verify.');
      return;
    }

    setLoading(true);
    setResult(null);

    const formData = new FormData();
    if (inputText) formData.append('text_content', inputText);
    if (selectedFile) {
      formData.append('file', {
        uri: selectedFile.uri,
        name: selectedFile.fileName || 'upload.jpg',
        type: selectedFile.mimeType || 'image/jpeg',
      } as any);
    }
    formData.append('preferred_language', preferredLanguage);

    try {
      const response = await fetch(`${BACKEND_URL}/api/v1/verify`, {
        method: 'POST',
        body: formData,
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      if (!response.ok) {
        throw new Error(`Server returned ${response.status}`);
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

  return (
    <ScrollView style={styles.container} contentContainerStyle={{ paddingBottom: 60 }}>
      <Text style={styles.header}>KAVACH AI</Text>
      <Text style={styles.subHeader}>Universal Scam & Legal Fraud Verifier</Text>

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
            {selectedFile ? '✓ Document / QR Attached' : '📁 Attach Notice / QR / Screenshot'}
          </Text>
        </TouchableOpacity>

        {/* Language selector */}
        <View style={styles.langRow}>
          <Text style={styles.langLabel}>Voice Warning:</Text>
          <TouchableOpacity
            style={[styles.langChip, preferredLanguage === 'hi' && styles.langChipActive]}
            onPress={() => setPreferredLanguage('hi')}
          >
            <Text style={[styles.langText, preferredLanguage === 'hi' && styles.langTextActive]}>हिंदी (Hindi)</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.langChip, preferredLanguage === 'en' && styles.langChipActive]}
            onPress={() => setPreferredLanguage('en')}
          >
            <Text style={[styles.langText, preferredLanguage === 'en' && styles.langTextActive]}>English</Text>
          </TouchableOpacity>
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
          <Text style={styles.confidence}>Confidence: {(result.confidence * 100).toFixed(0)}%</Text>
          <Text style={styles.summary}>{result.summary}</Text>

          <View style={styles.reasonsList}>
            {result.reasons.map((r: string, idx: number) => (
              <Text key={idx} style={styles.reasonText}>
                • {r}
              </Text>
            ))}
          </View>

          {/* Voice Memo & Family Escalation */}
          <TouchableOpacity style={styles.audioButton} onPress={playVoiceExplanation}>
            <Text style={styles.audioButtonText}>🔊 Play Audio Warning (Voice)</Text>
          </TouchableOpacity>

          {/* Cybercrime Dossier Button */}
          {result.dossier && (
            <TouchableOpacity style={styles.dossierButton} onPress={() => setShowDossierModal(true)}>
              <Text style={styles.dossierButtonText}>📋 View 1930 Cybercrime Dossier</Text>
            </TouchableOpacity>
          )}
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
});
