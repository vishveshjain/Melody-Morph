import os
import librosa
import numpy as np
import mido
from midi2audio import FluidSynth
from pydub import AudioSegment
import scipy.io.wavfile

# SoundFont path
SOUNDFONT_PATH = os.path.join(os.path.dirname(__file__), "soundfont.sf2")

def process_audio(input_path, instrument, output_dir):
    base_name = os.path.splitext(os.path.basename(input_path))[0]
    song_output_dir = os.path.join(output_dir, base_name)
    os.makedirs(song_output_dir, exist_ok=True)
    
    # 1. Load Audio
    print(f"Loading audio: {input_path}")
    y, sr = librosa.load(input_path, sr=22050, mono=True)
    
    # 2. Extract Melody (Pitch Tracking)
    print("Extracting melody...")
    f0, voiced_flag, voiced_probs = librosa.pyin(y, fmin=librosa.note_to_hz('C2'), fmax=librosa.note_to_hz('C6'))
    
    # 3. Convert to MIDI
    print("Converting to MIDI...")
    midi_path = os.path.join(song_output_dir, 'melody.mid')
    create_midi_from_pitch(f0, voiced_flag, midi_path)

    # 4. Synthesize MIDI
    print(f"Synthesizing {instrument}...")
    instrument_audio_path = os.path.join(song_output_dir, f'{instrument}.wav')
    
    instrument_map = {
        "Piano": 0,
        "Guitar": 24, 
        "Violin": 40,
        "Flute": 73,
        "Trumpet": 56
    }
    program = instrument_map.get(instrument, 73)
    
    synthesis_success = False
    if os.path.exists(SOUNDFONT_PATH):
        try:
            add_program_change(midi_path, program)
            fs = FluidSynth(sound_font=SOUNDFONT_PATH)
            fs.midi_to_audio(midi_path, instrument_audio_path)
            synthesis_success = True
        except Exception as e:
            print(f"FluidSynth failed: {e}")
    
    if not synthesis_success:
         print("Using fallback synthesizer.")
         generate_sine_wave_audio(f0, voiced_flag, instrument_audio_path, sr, instrument)

    # 5. Mix with Original
    print("Mixing tracks...")
    try:
        inst_audio = AudioSegment.from_wav(instrument_audio_path)
        try:
            original_audio = AudioSegment.from_file(input_path)
        except Exception:
            print("Could not load original audio. Returning instrument track only.")
            original_audio = None
        
        if original_audio:
            if len(inst_audio) > len(original_audio):
                inst_audio = inst_audio[:len(original_audio)]
            combined = original_audio.overlay(inst_audio)
        else:
            combined = inst_audio
        
        final_output = os.path.join(output_dir, f"{base_name}_{instrument}.wav")
        combined.export(final_output, format="wav")
        
    except Exception as e:
        print(f"Mixing failed: {e}")
        return instrument_audio_path
    
    return final_output

def create_midi_from_pitch(f0, voiced_flag, midi_path):
    mid = mido.MidiFile()
    track = mido.MidiTrack()
    mid.tracks.append(track)
    
    hop_length = 512
    sr = 22050
    time_per_frame = hop_length / sr
    ticks_per_frame = int(mido.second2tick(time_per_frame, mid.ticks_per_beat, 500000))
    
    last_note = None
    current_duration = 0
    
    for i, freq in enumerate(f0):
        if not voiced_flag[i] or np.isnan(freq):
            if last_note is not None:
                track.append(mido.Message('note_off', note=last_note, velocity=0, time=current_duration))
                last_note = None
                current_duration = ticks_per_frame
            else:
                current_duration += ticks_per_frame
        else:
            note = int(round(librosa.hz_to_midi(freq)))
            if note != last_note:
                if last_note is not None:
                    track.append(mido.Message('note_off', note=last_note, velocity=0, time=current_duration))
                    current_duration = 0
                track.append(mido.Message('note_on', note=note, velocity=100, time=current_duration))
                last_note = note
                current_duration = ticks_per_frame
            else:
                current_duration += ticks_per_frame
                
    if last_note is not None:
        track.append(mido.Message('note_off', note=last_note, velocity=0, time=current_duration))
        
    mid.save(midi_path)

def add_program_change(midi_path, program_number):
    mid = mido.MidiFile(midi_path)
    for track in mid.tracks:
        track.insert(0, mido.Message('program_change', program=program_number, time=0))
    mid.save(midi_path)

def generate_sine_wave_audio(f0, voiced_flag, output_path, sr=22050, instrument="Flute"):
    # 1. Fix Dropouts (Interpolation)
    f0_clean = np.copy(f0)
    nans = np.isnan(f0_clean)
    
    def interpolate_nans(x):
        nans = np.isnan(x)
        if np.all(nans): return np.zeros_like(x)
        if not np.any(nans): return x
        valid_indices = np.where(~nans)[0]
        x[nans] = np.interp(np.where(nans)[0], valid_indices, x[valid_indices])
        return x

    f0_clean = interpolate_nans(f0_clean)
    f0_clean = np.convolve(f0_clean, np.ones(5)/5, mode='same') # Smooth pitch

    # 2. Smooth Voiced Flag (Legato)
    voiced_clean = np.copy(voiced_flag)
    gap_limit = 10
    gap_count = 0
    in_gap = False
    gap_start = 0
    
    for i in range(len(voiced_clean)):
        if not voiced_clean[i]:
            if not in_gap:
                in_gap = True
                gap_start = i
            gap_count += 1
        else:
            if in_gap:
                if gap_count < gap_limit:
                    voiced_clean[gap_start:i] = True
                in_gap = False
                gap_count = 0

    total_samples = len(f0) * 512
    audio = np.zeros(total_samples)
    hop_length = 512
    
    # Instrument Definitions
    inst_type = "sine"
    harmonics = [1.0]
    decay = 1.0
    
    if instrument == "Flute":
        harmonics = [1.0, 0.2, 0.1]
        inst_type = "wind"
    elif instrument == "Piano":
        harmonics = [1.0, 0.5, 0.3, 0.2]
        inst_type = "pluck"
        decay = 1.5
    elif instrument == "Guitar":
        harmonics = [1.0, 1.0, 0.8, 0.6, 0.4]
        inst_type = "pluck"
        decay = 1.0
    elif instrument == "Violin":
        inst_type = "bowed"
    elif instrument == "Trumpet":
        inst_type = "brass"
    elif instrument == "Saxophone":
        inst_type = "sax"

    current_sample_idx = 0
    phases = np.zeros(10)
    
    last_freq = 0
    time_since_attack = 0
    active_amp = 0.0
    
    for i, freq in enumerate(f0_clean):
        is_voiced = voiced_clean[i]
        target_amp = 0.6 if is_voiced else 0.0
        frame_audio = np.zeros(hop_length)
        
        if inst_type == "pluck":
            if target_amp > 0 and abs(freq - last_freq) > freq * 0.05:
                time_since_attack = 0
                active_amp = 0.8
                last_freq = freq
            
            decay_factor = 3.0 / decay
            env = active_amp * np.exp(-decay_factor * (time_since_attack / sr))
            if env < 0.01: env = 0
            final_amp = env
            time_since_attack += hop_length
            
            for h, w in enumerate(harmonics):
                h_freq = freq * (h + 1)
                if h_freq < sr/2:
                    damp = 1.0 + (h * 8.0 * (time_since_attack/sr))
                    phase_inc = 2 * np.pi * h_freq / sr
                    frame_phases = phases[h] + np.arange(hop_length) * phase_inc
                    frame_audio += (w / damp) * np.sin(frame_phases)
                    phases[h] += hop_length * phase_inc
                    phases[h] %= 2 * np.pi
                    
        elif inst_type == "bowed":
            final_amp = target_amp
            if final_amp > 0:
                vib = 0.02 * np.sin(2 * np.pi * 6.0 * (current_sample_idx/sr))
                freq_mod = freq * (1 + vib)
                for h in range(1, 10):
                    h_freq = freq_mod * h
                    if h_freq < sr/2:
                        w = 1.0 / h
                        phase_inc = 2 * np.pi * h_freq / sr
                        frame_phases = phases[h-1] + np.arange(hop_length) * phase_inc
                        frame_audio += w * np.sin(frame_phases)
                        phases[h-1] += hop_length * phase_inc
                        phases[h-1] %= 2 * np.pi
                        
        elif inst_type == "brass":
            final_amp = target_amp
            if final_amp > 0:
                for h in range(1, 10, 2):
                    h_freq = freq * h
                    if h_freq < sr/2:
                        w = 1.0 / h
                        phase_inc = 2 * np.pi * h_freq / sr
                        frame_phases = phases[h-1] + np.arange(hop_length) * phase_inc
                        frame_audio += w * np.sin(frame_phases)
                        phases[h-1] += hop_length * phase_inc
                        phases[h-1] %= 2 * np.pi

        elif inst_type == "wind" or inst_type == "sax":
            final_amp = target_amp
            if final_amp > 0:
                phase_inc = 2 * np.pi * freq / sr
                frame_phases = phases[0] + np.arange(hop_length) * phase_inc
                frame_audio += np.sin(frame_phases)
                phases[0] += hop_length * phase_inc
                phases[0] %= 2 * np.pi
                
                noise = np.random.normal(0, 0.1, hop_length)
                noise = np.convolve(noise, np.ones(3)/3, mode='same')
                frame_audio += noise * (0.3 if inst_type == "sax" else 0.15)

        else:
            final_amp = target_amp
            if final_amp > 0:
                 phase_inc = 2 * np.pi * freq / sr
                 frame_phases = phases[0] + np.arange(hop_length) * phase_inc
                 frame_audio += np.sin(frame_phases)
                 phases[0] += hop_length * phase_inc
                 phases[0] %= 2 * np.pi

        if np.max(np.abs(frame_audio)) > 0:
            frame_audio = frame_audio / np.max(np.abs(frame_audio)) * final_amp
            
        audio[current_sample_idx : current_sample_idx+hop_length] = frame_audio
        current_sample_idx += hop_length

    # Post-Processing: Reverb
    delay_samples = int(0.05 * sr)
    decay = 0.3
    audio_reverb = np.zeros_like(audio)
    audio_reverb[:delay_samples] = audio[:delay_samples]
    for i in range(delay_samples, len(audio)):
        audio_reverb[i] = audio[i] + decay * audio_reverb[i - delay_samples]
    audio = audio_reverb

    # Smoothing
    audio = np.convolve(audio, np.ones(10)/10, mode='same')
            
    if np.max(np.abs(audio)) > 0:
        audio = audio / np.max(np.abs(audio)) * 0.9
    scipy.io.wavfile.write(output_path, sr, (audio * 32767).astype(np.int16))
