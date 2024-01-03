import librosa as rosa
import numpy as np
from enum import Enum
from json_tricks import dump, dumps, load, loads
import os
from typing import List, Tuple
import copy
import math
from pysndfx import AudioEffectsChain


class Audio:
	class AugmentationStep:
		class Steps(Enum):
			Nothing = "Raw"
			Mix = "Mix"
			Equalizer = "Equalizer"
			BandPass = "BandPass"
			BandReject = "BandReject"
			LowShelf = "LowShelf"
			HighSelf = "LowShelf"
			HighPass = "HighPass"
			LowPass = "LowPass"
			Limiter = "Limiter"
			Compressor = "Compressor"
			Delay="Delay"
			Overdrive="Overdrive"
			Phaser="Phaser"
			Pitch = "Pitch"
			Reverb = "Reverb"

		def __init__(self, audio: "Audio", step: Steps, parameters: dict):
			params = copy.deepcopy(parameters)
			self.setupDefaults(parameters=params, step=step)
			self.data = (audio.impl.getPath(), step.value, params)

		def __call__(self) -> Tuple[str, str, dict]:
			return self.data

		def setupDefaults(self, parameters: dict, step: "Audio.AugmentationStep.Steps"):
			if step is self.Steps.Pitch:
				if not ("shift" in parameters and parameters["shift"]):
					parameters["shift"] = False
				if not ("use_tree" in parameters and parameters["use_tree"]):
					parameters["use_tree"] = False
				if not ("segment" in parameters and parameters["segment"]):
					parameters["segment"] = 82
				if not ("search" in parameters and parameters["search"]):
					parameters["search"] = 14.68
				if not ("overlap" in parameters and parameters["overlap"]):
					parameters["overlap"] = 12
			if step is self.Steps.Reverb:
				if not ("reverberance" in parameters and parameters["reverberance"]):
					parameters["reverberance"] = 50
				if not ("hf_damping" in parameters and parameters["hf_damping"]):
					parameters["hf_damping"] = 50
				if not ("room_scale" in parameters and parameters["room_scale"]):
					parameters["room_scale"] = 100
				if not ("stereo_depth" in parameters and parameters["stereo_depth"]):
					parameters["stereo_depth"] = 100
				if not ("pre_delay" in parameters and parameters["pre_delay"]):
					parameters["pre_delay"] = 20
				if not ("wet_gain" in parameters and parameters["wet_gain"]):
					parameters["wet_gain"] = 0
				if not ("wet_only" in parameters and parameters["wet_only"]):
					parameters["wet_only"] = False

		def __add__(self, other: "Audio.AugmentationStep") -> "Audio.AugmentationStep":
			pass

	class AudioSegment:
		def __init__(self, begin: float = 0, end: float = -1, audio: "Audio" = None, samplingRate: int = None):
			self.begin = begin if begin is not None else 0
			self.end = end
			assert self.end is not -1 or (audio is not None and samplingRate is not None)
			if self.end is not -1:
				assert self.end > self.begin
			self.complete = False
			if audio is not None and samplingRate is not None:
				duration = rosa.get_duration(y=rosa.to_mono(audio.impl.getData()), sr=samplingRate)
				self.complete = (self.end == duration)
				if self.end is -1:
					self.complete = True
					self.end = duration

		def getBegin(self, samplingRate: int = 1) -> float:
			begin = self.begin * samplingRate
			return int(begin) if samplingRate != 1 else begin

		def isComplete(self):
			return self.complete

		def getEnd(self, samplingRate: int = 1) -> float:
			end = self.end * samplingRate
			return int(end) if samplingRate != 1 else end

		def getRange(self, samplingRate: int = 1) -> int:
			theRange = (self.getEnd(samplingRate) - self.getBegin(samplingRate))
			return int(theRange) if samplingRate != 1 else theRange

	class AudioImpl:
		class FittingMethod(Enum):
			Padding = "Padding"
			Looping = "Looping"

		def __init__(self, array: np.ndarray = None, samplingRate: int = None, path: str = None):
			assert (array is not None and samplingRate is not None) or path is not None
			self.array = array
			if self.array is not None:
				self.array = rosa.to_mono(self.array)
				rosa.util.valid_audio(self.array, mono=True)
			self.samplingRate = samplingRate
			self.path = path
			self.length = len(self.getData())
			self.duration = (rosa.get_duration(y=rosa.to_mono(self.getData()), sr=self.samplingRate))
			self.id = np.random.randint(0, 10 ** 10)

		def clone(self) -> "Audio.AudioImpl":
			return Audio.AudioImpl(array=copy.deepcopy(self.array), samplingRate=self.samplingRate, path=self.path)

		def getData(self) -> np.ndarray:
			if self.array is None:
				if self.path is not None:
					self.array, self.samplingRate = rosa.load(self.path, sr=None, mono=True)
					rosa.util.valid_audio(self.array, mono=True)
			return self.array

		def getClonedData(self) -> np.ndarray:
			return copy.deepcopy(self.getData())

		def setData(self, data: np.ndarray):
			assert data is not None
			self.array = data
			self.length = len(self.getData())
			self.duration = (rosa.get_duration(y=rosa.to_mono(self.getData()), sr=self.samplingRate))

		def __getSampleCountInNSeconds(self, n: float = 1) -> float:
			assert n is not None
			return n * self.samplingRate

		def getSamplingRate(self) -> int:
			return self.samplingRate

		def getPath(self) -> str:
			return self.path

		def getLength(self) -> int:
			return self.length

		def getDuration(self) -> int:
			return self.duration

		def getSlicedData(self, segment) -> np.ndarray:
			return self.getData()[segment.getBegin(samplingRate=self.getSamplingRate()):
								  segment.getEnd(samplingRate=self.getSamplingRate())]

		def getClonedSlicedData(self, segment) -> np.ndarray:
			return copy.deepcopy(self.getSlicedData(segment))

		def resample(self, targetRatio: float):
			assert targetRatio > 0
			if self.getSamplingRate() != targetRatio:
				self.setData(rosa.resample(self.array, self.getSamplingRate(), targetRatio))
				self.samplingRate = targetRatio

		def fitLength(self, length: int, fittingMethod: FittingMethod = FittingMethod.Padding):
			if length == len(self.getData()):
				return
			if length < self.getLength():
				self.slice(Audio.AudioSegment(begin=0, end=length))
				return
			if fittingMethod == Audio.AudioImpl.FittingMethod.Padding:
				self.setData(data=np.pad(array=self.getData(),
										 pad_width=(0, length - self.getLength()),
										 mode='constant', constant_values=(0,)))
			else:
				loopTours = math.ceil((length - self.getLength()) / float(self.getLength())) + 1
				self.setData(data=np.tile(self.getData(), loopTours))
				self.slice(Audio.AudioSegment(begin=0, end=length / self.getSamplingRate()))
				pass

		def align(self, segment: "Audio.AudioSegment"):
			theEnd = segment.getRange(self.getSamplingRate()) - self.getLength()
			self.setData(np.pad(array=self.getData(),
								pad_width=(segment.getBegin(self.getSamplingRate()),
										   theEnd),
								mode='constant', constant_values=(0,)))

		def normalize(self):
			self.setData(self.array / np.max(self.array))

		def gain(self, ratio: float = 1):
			self.setData(self.array * ratio)

		def write(self, path: str = None):
			pathToWrite = path
			if path is None:
				pathToWrite = self.getPath()
			rosa.output.write_wav(pathToWrite, self.getData(), self.getSamplingRate())


		def slice(self, segment: "Audio.AudioSegment"):
			self.setData(self.getSlicedData(segment))

	class Effect:
		def __init__(self, audio: "Audio", segmentsAsSeconds: List["Audio.AudioSegment"] = None, **options):
			assert segmentsAsSeconds is None or len(segmentsAsSeconds) > 1
			self.segment = segmentsAsSeconds[0]
			self.effectProcessor = AudioEffectsChain()
			self.audio = audio
			self.slice = audio.slice(segment=self.segment)
			self.parameters = options

		def __call__(self, step: "Audio.AugmentationStep.Steps", **options):
			effectExpression = {
				Audio.AugmentationStep.Steps.Equalizer:
					'self.effectProcessor.equalizer(frequency=int(options["frequency"]),q=float(options["q"]),db=float(options["db"]))',
				Audio.AugmentationStep.Steps.BandPass:
					'self.effectProcessor.bandpass(frequency=int(options["frequency"]),q=float(options["q"]))',
				Audio.AugmentationStep.Steps.BandReject:
					'self.effectProcessor.bandreject(frequency=int(options["frequency"]),q=float(options["q"]))',
				Audio.AugmentationStep.Steps.LowShelf:
					'self.effectProcessor.lowshelf(slope=float(options["slope"]),gain=float(options["gain"]),frequency=int(options["frequency"]))',
				Audio.AugmentationStep.Steps.HighSelf:
					'self.effectProcessor.highshelf(slope=float(options["slope"]),gain=float(options["gain"]),frequency=int(options["frequency"]))',
				Audio.AugmentationStep.Steps.HighPass:
					'self.effectProcessor.highpass(frequency=int(options["frequency"]),q=float(options["q"]))',
				Audio.AugmentationStep.Steps.LowPass:
					'self.effectProcessor.lowpass(frequency=int(options["frequency"]),q=float(options["q"]))',
				Audio.AugmentationStep.Steps.Limiter:
					'self.effectProcessor.limiter(gain=float(options["gain"]))',
				Audio.AugmentationStep.Steps.Compressor:
					'self.effectProcessor.compand(attack=float(options["attack"]),decay=int(options["decay"]),soft_knee=float(options["soft_knee"]),threshold=int(options["threshold"]),db_from=float(options["db_from"]),db_to=float(options["db_to"]))',
				Audio.AugmentationStep.Steps.Delay:
					'self.effectProcessor.delay(gain_in=float(options["gain_in"]),gain_out=float(options["gain_out"]),delays=options["delays"],decays=options["decays"],parallel=options["parallel"])',
				Audio.AugmentationStep.Steps.Overdrive:
					'self.effectProcessor.overdrive(gain=int(options["gain"]),colour=int(options["colour"]))',
				Audio.AugmentationStep.Steps.Phaser:
					'self.effectProcessor.phaser(gain_in=float(options["gain_in"]),gain_out=float(options["gain_out"]),delay=int(options["delay"]),decay=options["decay"],speed=int(options["speed"]),triangular=bool(options["triangular"]))',
				Audio.AugmentationStep.Steps.Pitch:
					'self.effectProcessor.pitch(options["shift"],use_tree=options["use_tree"],segment=options["segment"],search=options["search"],overlap=options["overlap"])',
			}.get(step, "Raw")
			self.effectProcessor = exec(effectExpression)
			self.slice.impl.setData(self.effectProcessor(src=self.slice))
			alignedWetAudio = self.slice.align(
				Audio.AudioSegment(begin=self.segment.begin, end=self.audio.getDuration()))
			pipeBuffer = (self.audio + alignedWetAudio)
			pipeBuffer.addPipeMetadata(
				Audio.AugmentationStep(audio=self.audio, step=step, parameters=self.parameters)())
			return pipeBuffer

	def __init__(self, data: AudioImpl, pipeSuffix: str = ""):
		self.impl = data
		self.pipeBuffer = self
		self.pipeSuffix = pipeSuffix
		self.pipeRecipe = []

	def addPipeMetadata(self, meta: Tuple[str, str, dict]):
		self.pipeSuffix += "|" + meta[1]
		self.pipeRecipe.append(meta)

	def getSegment(self, begin: float = 0, end: float = -1):
		return Audio.AudioSegment(audio=self, begin=begin, end=end, samplingRate=self.getSamplingRate())

	def getPipeRecipe(self) -> List:
		return self.pipeRecipe

	def clone(self, fresh: bool = False) -> "Audio":
		newOne = Audio(data=self.impl.clone())
		if not fresh:
			newOne.pipeSuffix = self.pipeSuffix
			newOne.pipeBuffer = self.pipeBuffer
			newOne.pipeRecipe = self.pipeRecipe
		return newOne

	def getOutput(self) -> "Audio":
		return self.pipeBuffer

	def slice(self, segment: "Audio.AudioSegment"):
		cloneOfThis = self.clone()
		cloneOfThis.impl.slice(segment)
		return cloneOfThis

	def resample(self, ratio: int) -> "Audio":
		cloneOfThis = self.clone()
		cloneOfThis.impl.resample(ratio)
		return cloneOfThis

	def getSamplingRate(self) -> int:
		return self.impl.getSamplingRate()

	def getLength(self) -> int:
		return len(self.impl.getData())

	def getDuration(self) -> int:
		return self.impl.getDuration()

	def fitLength(self, length: int, fittingMethod: "Audio.AudioImpl.FittingMethod" = AudioImpl.FittingMethod.Looping):
		cloneOfThis = self.clone()
		cloneOfThis.impl.fitLength(length=length, fittingMethod=fittingMethod)
		return cloneOfThis

	def fitDuration(self, duration: float,
					fittingMethod: "Audio.AudioImpl.FittingMethod" = AudioImpl.FittingMethod.Padding):
		cloneOfThis = self.clone()
		cloneOfThis.impl.fitLength(length=duration * self.getSamplingRate(), method=fittingMethod)
		return cloneOfThis

	def normalize(self):
		cloneOfThis = self.clone()
		cloneOfThis.impl.normalize()
		return cloneOfThis

	def align(self, segment: "Audio.AudioSegment"):
		cloneOfThis = self.clone()
		cloneOfThis.impl.align(segment)
		return cloneOfThis

	def gain(self, ratio: float = 1):
		cloneOfThis = self.clone()
		cloneOfThis.impl.gain(ratio)
		return cloneOfThis

	def add(self, other: "Audio", method: "Audio.AudioImpl.FittingMethod" = AudioImpl.FittingMethod.Looping) -> "Audio":
		fittedOther = other.fitLength(length=self.getLength(), fittingMethod=method)
		return Audio(
			data=Audio.AudioImpl(samplingRate=self.getSamplingRate(),
								 array=self.impl.getData() + fittedOther.impl.getData(),
								 path=self.impl.getPath()))

	def concat(self, other: "Audio") -> "Audio":
		return Audio(
			data=Audio.AudioImpl(samplingRate=self.getSamplingRate(),
								 array=np.concatenate((self.impl.getData(), other.impl.getData())),
								 path=self.impl.getPath()))

	def __add__(self, other: "Audio") -> "Audio":
		return self.add(other=other)

	def mix(self, other: "Audio" = None, segmentsAsSeconds: List[AudioSegment] = None, **options) -> "Audio":
		if other is None:
			return self.pipeBuffer
		assert segmentsAsSeconds is None or 0 < len(segmentsAsSeconds) < 3
		step = Audio.AugmentationStep(audio=other, step=Audio.AugmentationStep.Steps.Mix, parameters=options)
		if "weightOfMe" not in options:
			options["weightOfMe"] = 0.5
		if "weightOfOther" not in options:
			options["weightOfOther"] = 0.5
		if "fittingMethod" not in options:
			options["fittingMethod"] = Audio.AudioImpl.FittingMethod.Looping.value
		options["opponent"] = other.impl.getPath()
		resampledAndNormalizedOther = other.resample(ratio=self.getSamplingRate()).normalize()
		normalizedMe = self.normalize()
		pipeBuffer = None
		if segmentsAsSeconds is None:
			pipeBuffer = normalizedMe.gain(ratio=options["weightOfMe"]) + \
						 resampledAndNormalizedOther.fitLength(
							 length=self.getLength()).gain(ratio=options["weightOfOther"])
		else:
			if len(segmentsAsSeconds) < 2:
				segmentsAsSeconds *= 2
			me = normalizedMe.gain(ratio=options["weightOfMe"])
			mySlice = me.slice(segment=segmentsAsSeconds[0])
			othersSlice = resampledAndNormalizedOther.slice(segment=segmentsAsSeconds[1])
			othersFit = othersSlice.fitLength(length=segmentsAsSeconds[0].getRange(),
											  fittingMethod=Audio.AudioImpl.FittingMethod(options["fittingMethod"]))
			othersNormalized = othersFit.gain(ratio=options["weightOfOther"])
			mixOfUs = mySlice + othersNormalized
			alignedMix = mixOfUs.align(Audio.AudioSegment(begin=segmentsAsSeconds[0].begin, end=me.getDuration()))
			pipeBuffer = (me + alignedMix).normalize()
		pipeBuffer.addPipeMetadata(step())
		return pipeBuffer

	def write(self, customPath: str = None, description: bool = True):
		path = customPath if customPath is not None else os.path.dirname(self.impl.getPath())
		path += "/"
		name, extension = os.path.splitext(self.pipeBuffer.impl.getPath())
		name = os.path.basename(name)
		audioPath = path + name + self.pipeSuffix + extension
		self.pipeBuffer.impl.write(audioPath)
		if description:
			descriptionPath = path + name + self.pipeSuffix + ".json"
			with open(descriptionPath, 'w') as fp:
				dump(obj={"Steps": self.getPipeRecipe()}, fp=fp)


# audio1 = Audio(data=Audio.AudioImpl(path="sumeyracenet.wav"))
# audio2 = Audio(data=Audio.AudioImpl(path="cagrisesi.wav"))
# audio1.concat(audio2.resample(audio1.getSamplingRate())).write("./")
#audio1.mix(other=audio2,
#		   segmentsAsSeconds=[audio1.getSegment(begin=3, end=8), audio2.getSegment(begin=5, end=20)]).write(
#	"./")
# audio1 = Audio(data=Audio.AudioImpl(path="sumeyracenet.wav"))
# a = audio1.getSegment(4,7)
# print(a)

#audio1 = Audio(data=Audio.AudioImpl(path="/Users/app/Downloads/deneme/p243/p243_001.wav"))
#pitch = Audio.AugmentationStep(audio1, Audio.AugmentationStep.Steps.Pitch, parameters= {})
#pitched = audio1.Effect(audio1, **pitch()[2], segmentsAsSeconds=[audio1.getSegment(0,3),audio1.getSegment(3,6)])
#pitched(Audio.AugmentationStep.Steps.Pitch,**pitch()[2])