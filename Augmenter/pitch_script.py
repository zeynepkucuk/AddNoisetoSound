import argparse
import os
import time

import psutil
from pysndfx import AudioEffectsChain
from tqdm import tqdm

cpu_core_in_use = psutil.cpu_count(logical=True)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-dp", "--dataset-path", required=True, help="the path of dataset that has pure sound files")
    ap.add_argument("-sp", "--save-path", required=True, default='./output',
                    help="saving path of manipulated sound files")
    ap.add_argument("-pl", "--pitch-list", required=True, help="list of pitch shift numbers separated by ,")
    ap.add_argument("-wo", "--worker-count", required=False, help="")

    coreCount = psutil.cpu_count(logical=True)

    args = vars(ap.parse_args())

    sound_path = args["dataset_path"]
    save_path = args["save_path"]
    pitch_list = args["pitch_list"].split(',')

    cpu_core_in_use = coreCount if args["worker_count"] is None else args["worker_count"]

    pitch(sound_path, save_path, pitch_list)


def pitch(sound_path, save_path, pitch_list):
    """ The function that gets the sound files, and the list of pitch operations. Then applies the pitch operation on the
    sound files and save the new sound files to the given path.

    Parameters
    ----------
    sound_path: the path of sound files that will be pitched
    save_path: the saving path of newly pitched sound files.
    pitch_list: the list of pitch types that will be applied on the sounds

    Returns
    -------

    """
    filters = []
    names = []
    for pitch in pitch_list:
        fx = (
            AudioEffectsChain()
                .pitch(shift=pitch)
        )
        filters.append(fx)
        names.append("pitch_" + str(pitch))

    begin = time.time()

    for root, people, _ in os.walk(sound_path):
        length = len(people)
        print(length)
        # iterates each speaker folder in the path
        for index in range(length):
            person = people[index]
            for person_root, _, sound_files in os.walk(os.path.join(root, person)):
                # iterates each sound file of the speaker
                for sound_file in (x for x in sound_files if
                                   x.lower().endswith(".wav") or x.lower().endswith(".mp3") or x.lower().endswith(
                                       ".flac")):
                    try:
                        infile = os.path.join(person_root, sound_file)
                        os.makedirs(os.path.join(save_path, person), exist_ok=True)

                        for i in range(0, 6):
                            name = names[i] + "_" + sound_file
                            outfile = os.path.join(save_path, person, name)
                            filters[i](infile, outfile)
                    except Exception as e:
                        print("\nError: ", e)
                        print("person: {0}, filename: {1}".format(person_root, sound_file))

    end = time.time()

    print(end - begin)

if __name__ == "__main__":
    main()
