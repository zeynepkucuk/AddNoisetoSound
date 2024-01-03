from pydub import AudioSegment
from pysndfx import AudioEffectsChain


def wav_file_save_helper(sound_data, save_path, save_sampling_rate):
    """ saves the given sound file to given path by applying given sampling rate.

    Parameters
    ----------
    sound_data: sound file that is represented as array
    save_path: the path that the sound file will be exported.
    save_sampling_rate: the sampling rate of sound file that will be exported.

    Returns
    -------

    """
    if save_path is not None and save_sampling_rate is not None:
        librosa.output.write_wav(save_path, sound_data, save_sampling_rate)
    elif save_path is not None:
        raise ValueError('if save_path is not None, save_sampling_rate must be specified')


def mix_pydub(sound_paths, save_path=None, save_format="wav", loop=True):
    """ Bu fonksiyon pydub AudioSegment nesnesi kullanarak verilen ses dosyalarını karıştırır ve
    oluşan ses dosyasını AudioSegment formatında doner.

    :param sound_paths: karıştırılacak ses dosyalarının bulunduğu dizinlerin listesi
    :param save_path: eğer oluşan ses dosyası herhangibir dizine kayıt edilecekse, ilgili dizin
    :param save_format: kayıt edilecek ses dosyasınn formatı (ör. "wav", "mp3" v.b)
    :param loop: ses dosyaları aynı uzunlukta olmadığında, artan kısma kısa sesin tekrardan yazılması
    :return:
    """

    if len(sound_paths) < 2:
        raise ValueError("There must be at least 2 sound files to mix")

    # read sound file and create a (sound_file, duration) tuple for sorting
    sounds = []
    for path in sound_paths:
        sound = AudioSegment.from_file(path)
        sounds.append((sound, sound.duration_seconds))
    # sort the sound files according to their duration
    sorted_sounds = sorted(sounds, key=lambda x: x[1], reverse=True)

    overlaid_sound = sorted_sounds[0][0]  # get the first sound which is the longest one
    for sound in sorted_sounds[1:]:  # iterate other sound files and overlay one by one
        overlaid_sound = overlaid_sound.overlay(sound[0], loop=loop)

    # save the overlaid sound file to specified path
    if save_path is not None:
        overlaid_sound.export(save_path, format=save_format)

    return overlaid_sound


# pydub mix  kod ornegi
# audio = mix_pydub(['./refikabirgul.wav', './efsacakir.wav', './noise-free-sound-0021.wav'],
# save_path="./dsfsdddf.wav")


def mix_librosa(sound1_data, sound2_data, save_path=None, save_sampling_rate=None):
    """ Bu fonksiyon librosa ses dataları alarak sesleri karıştırma işlemi yapar. Verilen ayarlara gore istenilen dizine,
    istenilen sampling_rate degeri ile dosya kayıt eder.

    :param sound1_data: ilk sesin librosa ile çıkartılmış data array'i
    :param sound2_data: ikinci sesin librosa ile çıkartılmış data array'i
    :param save_path: eğer olusan ses herhangi bir dizine kaydedilecekse dizin girilir, yoksa boş bırakılır.
    :param save_sampling_rate:  eğer oluşan ses kaydedilecekse, hangi sampling_rate ile kaydedilecegi bilgisi girilir
    :return: karıştırılmış librosa data array'i sonuç olarak döndürülür.
    """
    # ikinci ses birinci ses'den daha kısa ise kendini tekrarlayarak uzatılır.
    if len(sound1_data) >= len(sound2_data):
        while len(sound1_data) >= len(sound2_data):
            sound2_data = np.append(sound2_data, sound2_data)
    # uzatılan ikinci ses verisi birinci ses verisi ile eşit uzunluğa getirilir.
    sound2_cropped = sound2_data[0: len(sound1_data)]

    # iki sesin overlap işlemleri
    sound1_power = np.sum(sound1_data ** 2)
    sound2_power = np.sum(sound2_cropped ** 2)
    overlaid_sound = sound1_data + np.sqrt(sound1_power / sound2_power) * sound2_cropped

    # if specified, saves the wav file
    wav_file_save_helper(overlaid_sound, save_path, save_sampling_rate)

    return overlaid_sound


# librosa mix  ornegi
# orig, sr = librosa.load('./refikabirgul.wav')
# noise, sr = librosa.load('./noise-free-sound-0021.wav')
# mix_librosa(orig, noise, save_path='./mixed.wav', save_sampling_rate=sr)


def reverb_librosa(sound_data, save_path=None, save_sampling_rate=None, reverberance=50, hf_damping=50, room_scale=100,
                   stereo_depth=100, pre_delay=20, wet_gain=0, wet_only=False):
    """ Bu fonksiyon librosa ses datalarını alarak reverb (yankı) ekleme işlemi yapmaktadır.
    Eğer save_path ve sampling rate degerleri verilmiş ise ilgili bilgiler ile oluşan yeni dosyayı kaydeder.
    Reverb ile ilgili parametreleri kullanarak gerekli reverb ayarlarının yapılmasına müsade eder.

    :param sound_data: reverb eklenecek sesin librosa ile çıkartılmış data array degerleri.
    :param save_path: eğer olusan ses herhangi bir dizine kaydedilecekse dizin girilir, yoksa boş bırakılır.
    :param save_sampling_rate: eğer oluşan ses kaydedilecekse, hangi sampling_rate ile kaydedilecegi bilgisi girilir
    :param reverberance:
    :param hf_damping:
    :param room_scale:
    :param stereo_depth:
    :param pre_delay:
    :param wet_gain:
    :param wet_only:
    :return:
    """
    # reverb işlemi için gereken chain yapılı nesne oluşturulur.
    reverber = (
        AudioEffectsChain().reverb(reverberance=reverberance,
                                   hf_damping=hf_damping,
                                   room_scale=room_scale,
                                   stereo_depth=stereo_depth,
                                   pre_delay=pre_delay,
                                   wet_gain=wet_gain,
                                   wet_only=wet_only)
    )

    # ilgili ses dosyası için reverb işlemi yapılır.
    reverbed_sound_data = reverber(sound_data)

    # if specified, saves the wav file
    wav_file_save_helper(reverbed_sound_data, save_path, save_sampling_rate)

    return reverbed_sound_data


# reverb örnegi
# orig, sr = librosa.load('./efsacakir.wav', sr=None)
# reverb_librosa(orig, save_path='./reverbed1.wav', save_sampling_rate=sr)


def equalizer_librosa(sound_data, frequency, save_path=None, save_sampling_rate=None, q=1.0, db=-3.0):
    equalizer = (
        AudioEffectsChain().equalizer(frequency, q=q, db=db)
    )

    equalized_sound_data = equalizer(sound_data, frequency)

    # if specified, saves the wav file
    wav_file_save_helper(equalized_sound_data, save_path, save_sampling_rate)

    return equalized_sound_data


# equalizer örnegi
# orig, sr = librosa.load('./efsacakir.wav', sr=44100)
# equalizer_librosa(orig, 1, save_path='./equalized.wav', save_sampling_rate=sr)


def bandpass_librosa(sound_data, frequency, save_path=None, save_sampling_rate=None, q=1.0):
    """ Applies the band pass filter on the given sound file.

    Parameters
    ----------
    sound_data
    frequency
    save_path
    save_sampling_rate
    q

    Returns
    -------

    """
    bandpasser = (
        AudioEffectsChain().bandpass(frequency, q=q)
    )

    bandpassed_sound_data = bandpasser(sound_data, frequency)

    # if specified, saves the wav file
    wav_file_save_helper(bandpassed_sound_data, save_path, save_sampling_rate)

    return bandpassed_sound_data


# bandpass örnegi
# orig, sr = librosa.load('./efsacakir.wav', sr=16000)
# bandpass_librosa(orig, sr//5, save_path='./bandpassed.wav', save_sampling_rate=sr)


def white_noise_librosa(sound_data, mean=0, std=1, noise_factor=0.009, save_path=None, save_sampling_rate=None):
    """ Noise addition using normal distribution with mean = 0 and std =1
    Permissible noise factor value = x > 0.004
    Bu fonksiyonun default parametreleri white noise olacak sekilde ayarlanmıştır.

    :param sound_data:librosa sound data array
    :param mean:
    :param std:
    :param noise_factor:
    :param save_path:
    :param save_sampling_rate:
    :return: librosa sound data array
    """
    sound_data = sound_data + noise_factor * np.random.normal(mean, std, len(sound_data))

    # if specified, saves the wav file
    wav_file_save_helper(sound_data, save_path, save_sampling_rate)

    return sound_data


# white noise örnegi
# orig, sr = librosa.load('./efsacakir.wav', sr=None)
# white_noise_librosa(orig, save_path='./white_noised.wav', save_sampling_rate=sr)


def pitch_shift_librosa(sound_data, sr, n_steps=2, save_path=None, save_sampling_rate=None):
    """ Bu fonksiyon ses'e pitch(perdeleme) işlemi uyguluyor. Bir diğer deyişle sesi robotikleştiriyor.
    Input olarak librosa data array ve aynı sesin sampling rate degeri verilmesi gerekiyor. Diğer önemli parametre
    ise n_steps değeri. Bu değer arttırıldıkça ses daha çok robotikleşiyor.

    :param sound_data: librosa data array
    :param sr: ilgili data array'in sampling rate degeri
    :param n_steps: robotikleştirme oranı, arttıkça daha fazla robotikleşiyor
    :param save_path:
    :param save_sampling_rate:
    :return:
    """
    sound_data = librosa.effects.pitch_shift(sound_data, sr, n_steps=n_steps)

    # if specified, saves the wav file
    wav_file_save_helper(sound_data, save_path, save_sampling_rate)

    return sound_data


# pitch shift örnegi
# orig, sr = librosa.load('./efsacakir.wav', sr=None)
# pitch_shift_librosa(orig, sr, n_steps=2, save_path='./pitch_shift2.wav', save_sampling_rate=sr)
# pitch_shift_librosa(orig, sr, n_steps=1, save_path='./pitch_shift1.wav', save_sampling_rate=sr)
# pitch_shift_librosa(orig, sr, n_steps=3, save_path='./pitch_shift3.wav', save_sampling_rate=sr)
# pitch_shift_librosa(orig, sr, n_steps=4, save_path='./pitch_shift4.wav', save_sampling_rate=sr)
# pitch_shift_librosa(orig, sr, n_steps=5, save_path='./pitch_shift5.wav', save_sampling_rate=sr)
# pitch_shift_librosa(orig, sr, n_steps=6, save_path='./pitch_shift6.wav', save_sampling_rate=sr)

def reverse_librosa(sound_data, save_path=None, save_sampling_rate=None):
    """ Bu fonksiyon librosa ses datalarını alarak reverse (sesi ters çevirme)  işlemi yapmaktadır.
    Eğer save_path ve sampling rate degerleri verilmiş ise ilgili bilgiler ile oluşan yeni dosyayı kaydeder.

    :param sound_data: reverb eklenecek sesin librosa ile çıkartılmış data array degerleri.
    :param save_path: eğer olusan ses herhangi bir dizine kaydedilecekse dizin girilir, yoksa boş bırakılır.
    :param save_sampling_rate: eğer oluşan ses kaydedilecekse, hangi sampling_rate ile kaydedilecegi bilgisi girilir
    :return:
    """
    # reverse işlemi için gereken chain yapılı nesne oluşturulur.
    reverser = (
        AudioEffectsChain().reverse()
    )

    # ilgili ses dosyası için reverse işlemi yapılır.
    reversed_sound_data = reverser(sound_data)

    # if specified, saves the wav file
    wav_file_save_helper(reversed_sound_data, save_path, save_sampling_rate)

    return reversed_sound_data


# reverse örnegi
# orig, sr = librosa.load('./efsacakir.wav', sr=None)
# reverse_librosa(orig, save_path='./reversed.wav', save_sampling_rate=sr)

def change_speed_librosa(sound_data, save_path=None, save_sampling_rate=None,
                         factor=250, use_semitones=True):
    """ Bu fonksiyon librosa ses datalarını alarak change speed işlemi yapmaktadır.
    Eğer save_path ve sampling rate degerleri verilmiş ise ilgili bilgiler ile oluşan yeni dosyayı kaydeder.
    change speed ile ilgili parametreleri kullanarak gerekli change speed ayarlarının yapılmasına müsade eder.

    :param sound_data: hızı değişecek sesin librosa ile çıkartılmış data array degerleri.
    :param save_path: eğer olusan ses herhangi bir dizine kaydedilecekse dizin girilir, yoksa boş bırakılır.
    :param save_sampling_rate: eğer oluşan ses kaydedilecekse, hangi sampling_rate ile kaydedilecegi bilgisi girilir
    :param factor: Hızlandırmak icin pozitif yavaşlatmak için negatif değer verilmeli
    :param use_semitones:

    :return:
    """
    # speed işlemi için gereken chain yapılı nesne oluşturulur.
    speed_changer = (
        AudioEffectsChain().speed(factor=factor, use_semitones=use_semitones)
    )

    # ilgili ses dosyası için reverb işlemi yapılır.
    speed_changed_sound_data = speed_changer(sound_data)

    # if specified, saves the wav file
    wav_file_save_helper(speed_changed_sound_data, save_path, save_sampling_rate)

    return speed_changed_sound_data


# speed örnegi
# orig, sr = librosa.load('./efsacakir.wav', sr=None)
# change_speed_librosa(orig, factor=-300,use_semitones=True,save_path='./slower.wav', save_sampling_rate=sr)
# change_speed_librosa(orig, factor=300,use_semitones=True,save_path='./faster.wav', save_sampling_rate=sr)


import librosa
import numpy as np
from scipy.signal import butter, lfilter


def butter_lowpass(cutoff, fs, order=5):
    #  Cutoff: cutoff frequency
    #  Fs sampling rate
    nyq = 0.5 * fs  # Signal frequency
    normal_cutoff = cutoff / nyq  # Normal cutoff frequency = cutoff frequency / signal frequency
    b, a = butter(order, normal_cutoff, btype='lowpass', analog=False)
    return b, a


def butter_lowpass_filter(data, cutoff, fs, order=5):
    b, a = butter_lowpass(cutoff, fs, order=order)
    y = lfilter(b, a, data)
    return y  # Filter requirements.


def low_pass_filter_librosa(sound_data, sr, cutoff=1000, order=5, save_path=None, save_sampling_rate=None):
    filtered_sound_data = butter_lowpass_filter(sound_data, cutoff, sr, order)
    wav_file_save_helper(filtered_sound_data, save_path, save_sampling_rate)


# order = 5
# cutoff = 4000
# data, sr = librosa.load("./efsacakir.wav")
# low_pass_filter_librosa(data, sr, cutoff=4000, order=5, save_path='./5order_4000cutoff.wav', save_sampling_rate=sr)
# low_pass_filter_librosa(data, sr, cutoff=2000, order=5, save_path='./5order_2000cutoff.wav', save_sampling_rate=sr)
# low_pass_filter_librosa(data, sr, cutoff=1000, order=5, save_path='./5order_1000cutoff.wav', save_sampling_rate=sr)
# low_pass_filter_librosa(data, sr, cutoff=500, order=5, save_path='./5order_500cutoff.wav', save_sampling_rate=sr)


def butter_bandpass(low_cut, high_cut, sr, order=5):
    nyq = 0.5 * sr
    low = low_cut / nyq
    high = high_cut / nyq
    b, a = butter(order, [low, high], btype='band')
    return b, a


def butter_bandpass_filter(sound_data, sr, low_cut, high_cut, order=5):
    b, a = butter_bandpass(low_cut, high_cut, sr, order=order)
    y = lfilter(b, a, sound_data)
    return y


def band_pass_filter_librosa(sound_data, sr, low_cut=1024, high_cut=7000, order=5, save_path=None, save_sampling_rate=None):
    filtered_sound_data = butter_bandpass_filter(sound_data, sr, low_cut, high_cut, order=order)
    wav_file_save_helper(filtered_sound_data, save_path, save_sampling_rate)


#order = 5
#low_cut = 1024
#high_cut = 7000
#data, sr = librosa.load("./efsacakir.wav")
#band_pass_filter_librosa(data, sr, low_cut=1024, high_cut=7000, order=5, save_path='./bandpass_5order_1024low_7000high.wav',
#                         save_sampling_rate=sr)
# band_pass_filter_librosa(data, sr, low_cut=2000,high_cut=2000, order=5, save_path='./5order_low_high.wav', save_sampling_rate=sr)
# band_pass_filter_librosa(data, sr, low_cut=1000,high_cut=1000, order=5, save_path='./5order_low_high.wav', save_sampling_rate=sr)
# band_pass_filter_librosa(data, sr, low_cut=500, high_cut=500, order=5, save_path='./5order_low_high.wav', save_sampling_rate=sr)
