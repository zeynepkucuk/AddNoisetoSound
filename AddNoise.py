import argparse
import os
import random

import psutil
from Augmenter.Augmenter import Audio

cpu_core_in_use = psutil.cpu_count(logical=True)

def advanced_noise_injection(sound_path, noise_path, save_path, percentage: int = 20,
                             copy_remaining_sounds: bool = False):
    """ sound_path dizini altında verilen kişilerin sesleri ile noise_path dizini altında verilen noise'lar mix'lenir.
    Mix'lenmiş sesler save_path alanında verilen dizine kaydedilir. Mixleme işlemi yapılırken her bir wav dosyasının
    percentage kadar uzunluğuna noise eklenir.
    sound_path dizini altında klasörler bulunur, bu klasörler speaker adına karşılık gelir. Bu speaker dizini
    altında da wav veya mp3 dosyaları bulunur.
    noise_path dizini altında ise klasörler bulunMAZ. Sadece ilgili noise wav veya mp3 dosyaları bulunur.
    :param sound_path: seslerin olduğu dizin
    :param noise_path: noise'ların oldugu dizin
    :param save_path:  yeni seslerin kaydedileceği dizin
    :percentage: seslerin yuzde kacına noise eklenecegi bilgisi girilir
    """
    # percentage range check
    if percentage < 0 or percentage > 100:
        return

    noises = {}

    for root, people, _ in os.walk(sound_path):
        noise_start_at = 0
        # iterates each speaker folder in the path
        for person in people:
            for person_root, _, sound_files in os.walk(os.path.join(root, person)):
                # iterates each sound file of the speaker
                for sound_file in (x for x in sound_files if
                                   x.lower().endswith(".wav") or x.lower().endswith(".mp3") or x.lower().endswith(
                                       ".flac")):

                    # read current sound file
                    sound = Audio(data=Audio.AudioImpl(path=os.path.join(person_root, sound_file)))
                    sr = sound.getSamplingRate()  # gets the sampling rate of the sound
                    duration = sound.getDuration()  # gets the duration of the sound
                    noised_sound_duration = (duration / 100) * percentage  # calculates the noise length of the sound
                    # picks a random start time to add noise
                    start_at = random.uniform(0, duration - noised_sound_duration)

                    # read noise sound and concatenate them corresponding to sampling rate of sound
                    if str(sr) not in noises:
                        noises[str(sr)] = load_noise_sound_and_concatenate(noise_path, sr=sr)

                    # gets the total duration of concatenated noises
                    noise_duration = noises[str(sr)].getDuration()
                    # create corresponding path for saving the noised sound
                    os.makedirs(os.path.join(save_path, person), exist_ok=True)

                    # when there is no enough noises left
                    if noise_start_at + noised_sound_duration > noise_duration:
                        remaining_duration = noise_duration - noise_start_at  # finds the remaining noise duration
                        # iterates till the noising process done
                        while noised_sound_duration > 0:
                            # when there is no enough noise duration for mixing
                            if remaining_duration < noised_sound_duration:
                                # mixes the remaining noise into sound
                                sound = sound.mix(other=noises[str(sr)], segmentsAsSeconds=[
                                    sound.getSegment(begin=start_at, end=start_at + remaining_duration),
                                    noises[str(sr)].getSegment(begin=noise_start_at,
                                                               end=noise_start_at + remaining_duration)])
                                start_at += remaining_duration  # last index of the added noise on sound
                                noised_sound_duration -= remaining_duration  # duration of noise that is left
                                noise_start_at = 0  # noise sound is just finish, and operation start from beginning
                                remaining_duration = noise_duration - noise_start_at
                            else:  # when the noise duration is enough
                                # mixes the noise, which has enough duration, into sound
                                sound.mix(other=noises[str(sr)], segmentsAsSeconds=[
                                    sound.getSegment(begin=start_at, end=start_at + noised_sound_duration),
                                    noises[str(sr)].getSegment(begin=noise_start_at,
                                                               end=noise_start_at + noised_sound_duration)]).write(
                                    os.path.join(save_path, person))

                                noise_start_at += noised_sound_duration  # set the index of remaining noise
                                noised_sound_duration = 0
                                """
                                
                                     else if: 
                                    sound.mix(other=noises[str(sr),segmentsAsSeconds=[
                                        sound.getDuration((begin=start_at) +noised_sound_duration),
                                        noises[str(sr),segmentsAsSeconds=[os.path.gets]]
                                    ]])
                            """

                    else:
                        sound.mix(other=noises[str(sr)],
                                  segmentsAsSeconds=[
                                      sound.getSegment(begin=start_at, end=start_at + noised_sound_duration),
                                      noises[str(sr)].getSegment(begin=noise_start_at,
                                                                 end=noise_start_at + noised_sound_duration)]).write(
                            os.path.join(save_path, person))

                        # changes the noise sound start point for next iteration
                        noise_start_at += noised_sound_duration


def load_noise_sound_and_concatenate(path, sr):
    """ Bu fonksiyon verilen bir dizin altında bulunan wav veya mp3 dosyalarını tek tek okuyup,
    data array'ini peşpeşe tek bir listeye ekler.
    :param path: seslerin okunacağı dizin
    :param sr: seslerin okunacağı sampling rate degeri
    :return: seslerin librosa ile okunmuş numpy array değerlerinin bulunduğu bir list
    """
    sound_list = []
    for root, _, sound_files in os.walk(path):
        sound_list = None
        for sound_file in (x for x in sound_files if
                           x.lower().endswith(".wav") or x.lower().endswith(".mp3") or x.lower().endswith(".flac")):
            if sound_list == None:
                sound_list = Audio(data=Audio.AudioImpl(path=os.path.join(root, sound_file), samplingRate=sr))
            else:
                sound_list = sound_list.concat(
                    Audio(data=Audio.AudioImpl(path=os.path.join(root, sound_file), samplingRate=sr)))

    return sound_list


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-dp", "--dataSet-path", required=True, help="the sounds that is mixed by noises")
    ap.add_argument("-np", "--noise-path", required=True, help="the path of noise sound that is mixed on sounds.")
    ap.add_argument("-sp", "--save-path", required=True, help="the path that the noised sounds will be saved")
    ap.add_argument("-p", "--percentage", required=True, default=20,
                    help="the percentage of dataset that is mixed by noises")
    ap.add_argument("-wo", "--worker-count", required=False, help="")
    args = vars(ap.parse_args())

    coreCount = psutil.cpu_count(logical=True)
    sound_path = args["dataSet_path"]
    noise_path = args["noise_path"]
    save_path = args["save_path"]
    percentage = int(args["percentage"])

    cpu_core_in_use = coreCount if args["worker_count"] is None else args["worker_count"]

    advanced_noise_injection(sound_path,
                             noise_path,
                             save_path,
                             percentage=percentage)


if __name__ == "__main__":
    main()
