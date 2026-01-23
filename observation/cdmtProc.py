import os
import argparse
import sigpyproc as spp
from psrqpy import Pulsar
import tqdm
import re

import numpy as np
from numpy.lib import stride_tricks
from itertools import groupby
from operator import itemgetter
import warnings
warnings.filterwarnings('ignore')

def exploreFolderTree(path, ext = 'zst', requires = '16130'):
	returnList = []
	relReturnList = []
	for base, dirs, files in os.walk(path):
		for file in files:
			if ext == file.split('.')[-1] and requires in file.split('/')[-1]:
				returnList.append(os.path.abspath(os.path.join(base, file)))
				relReturnList.append(base.replace(path, ''))

	return returnList, relReturnList

def outputPath(fil, rel, source, args):
	if args.structure:
		outputFile = rel
	else:
		outputFile = ""

	outputFilePath = os.path.join(args.output, outputFile)
	timeSubstr = re.search(r"\d{4}-\d{2}-\d{2}[T]\d{2}:\d{2}:\d{2}", fil).group(1)
	outputPrefix = f"{source}_{timeSubStr}_"

	return os.path.join(outputFilePath, outputPrefix)


cdmtParams = {
	'0': '-f 10 -n 8192',
	'55': '-f 10 -n 12288',
	'82': '-f 10 -n 16384',
	'110': '-f 5 -N 131072 -n 20480',
	'138': '-f 5 -N 131072 -n 24576',
	'165': '-f 5 -N 131072 -n 28672',
	'193': '-f 5 -N 131072 -n 32768',
	'221': '-f 2 -N 262144 -n 36864',
	'248': '-f 2 -N 262144 -n 40960',
	'276': '-f 2 -N 262144 -n 45056',
	'304': '-f 2 -N 262144 -n 49152',
	'331': '-f 2 -N 262144 -n 53248',
	'359': '-f 2 -N 262144 -n 57344',
	'387': '-f 2 -N 262144 -n 61440',
	'414': '-f 2 -N 262144 -n 65536',
	'tooHigh': '-f 1 -N 524288 -n 131072'
}

dmDict = {}

alias = {'Crab': 'B0531+21'}


def generateCDMTCmds(rawUdps, relPaths, sources, args):
	cdmtCmds = []
	cdmtFils = []
	for raw, rel, source in tqdm.tqdm(sorted(list(zip(rawUdps, relPaths, sources))), total = len(sources)):
		print(raw, rel, source)
		if source == "CrabBroken":
			continue
		inputUdp = raw.replace(args.port, '%d')
		header = os.path.join(args.hdrs, source + ".sigprochdr")
		print(header)
		if not os.path.exists(header):
			#raise RuntimeError(f"Unable to find header for {source} as {header}; exiting.")
			print("NOHDR")

		if args.structure:
			outputFile = rel
		else:
			outputFile = ""

		outputFile = os.path.join(os.path.join(args.output, outputFile), f"{source}_{raw.split('/')[-1].split('.')[-3]}")


		try:
			if len(dmDict) == 0:
				with open(os.path.join(args.hdrs, "dmFallback.txt"), 'r') as ref:
					dms = ref.readlines()
					for line in dms:
						filSource, dm = line.split()
						dmDict[filSource] = float(dm)

			dm = dmDict[source]
		except Exception:
			print(f"{source} not in dmFallback.txt, continuing")
			if source in alias.keys():
				source = alias[source]
			dm = Pulsar(source)['dm']


		dm = float(dm)
		if dm < 30:
			cdmtParam = cdmtParams['0']
		elif dm < 82.9:
			cdmtParam = cdmtParams['55']
		elif dm < 110.6:
			cdmtParam = cdmtParams['82']
		elif dm < 138.1:
			cdmtParam = cdmtParams['110']
		elif dm < 165.8:
			cdmtParam = cdmtParams['138']
		elif dm < 193.6:
			cdmtParam = cdmtParams['165']
		elif dm < 221.2:
			cdmtParam = cdmtParams['193']
		elif dm < 248.9:
			cdmtParam = cdmtParams['221']
		elif dm < 276.6:
			cdmtParam = cdmtParams['248']
		elif dm < 304.2:
			cdmtParam = cdmtParams['276']
		elif dm < 331.9:
			cdmtParam = cdmtParams['304']
		elif dm < 359.5:
			cdmtParam = cdmtParams['331']
		elif dm < 387.1:
			cdmtParam = cdmtParams['359']
		elif dm < 414.9:
			cdmtParam = cdmtParams['387']
		elif dm < 442.5:
			cdmtParam = cdmtParams['414']
		else:
			print("That DM is a a bit higher than previously tested parameters, defaulting to the highest value available.")
			cdmtParam = cdmtParams['tooHigh']
		cdmtFil = f"{outputFile}_cDM{dm:06.2f}_P000.fil"
		if not os.path.exists(cdmtFil):
			cdmtCmds.append(f"# {source} - {raw.split('/')[-1].split('.')[-3]} - DM={dm} \ncdmt_udp {inputUdp} -o {outputFile} -d {dm},0,1 -b {args.deci} -a -m {header} {cdmtParam}\n\n")
			cdmtFils.append(cdmtFil)

	return cdmtCmds, cdmtFils

def generateDigifilCmds(inputFils, args):
	return [f"digifil -b 8 {fil} -o {fil.replace('.fil', '_8bit.fil')}\n" for fil in inputFils], [f"{fil.replace('.fil', '_8bit.fil')}" for fil in inputFils]

"""
def generateIQRMCmds(inputFils, args):
	return [f"iqrm_apollo_cli -i {fil} -o {fil.replace('.fil', '_iqrm.fil')} {args.iqrm_args}" for fil in inputFils], [f"{fil.replace('.fil', '_iqrm.fil')}" for fil in inputFils]

def generatePlotCmds(inputFils, relPaths, sources, args):
	quickPlotCmds = []
	for fil, rel, source in zip(inputFils, relPaths, sources):
		outputPrefix = outputPath(fil, rel, source, args)
		quickPlotCmds.append(f"filQuickPlot.py -i {fil} -o {outputPrefix}_timeseries/{outputPrefix.split('/')[-1]} {args.plot_args}")

	return quickPlotCmds

"""


def grouping(sequentialList):
	# Don't feel like bothering to setup an iterator
	outputList = []
	for __, group in groupby(enumerate(sequentialList), lambda idx: idx[0] - idx[1]):
		tmpList = list(map(itemgetter(1), group))
		tmpList.sort()
		outputList.append([tmpList[0][0], tmpList[-1][0]])
	return outputList

def rfiZapping(pulseProfile, zappedChans = np.arange(3700, 3904), gui = False, chanGroup = 8, windowSize = 16, std = 3., bandpassPassed = False):
	if bandpassPassed:
		bandpass = pulseProfile.copy()
	else:
		bandpass = pulseProfile.get_bandpass()

	rawBandpass = bandpass.copy()
	zapChans = np.zeros(bandpass.size)
	zapChans[zappedChans] = 1
	rfiMax = np.percentile(bandpass, 83)
	rfiMax *= 2.
	zapChans += bandpass > rfiMax

	discardLength = int(windowSize * chanGroup * 0.5)
	wordsize = bandpass.dtype.itemsize
	data_strided = stride_tricks.as_strided(bandpass[discardLength: -discardLength], shape = (bandpass[discardLength: -discardLength].size, windowSize * chanGroup), strides = (wordsize, wordsize))
	
	testVal = np.percentile(data_strided, 66, axis = 1)
	stDev = np.hstack([np.std(data_strided[idx, testVal[idx] > data_strided[idx, :]]) for idx in range(data_strided.shape[0])])

	zapChans[:discardLength] = 1
	zapChans[-discardLength:] = 1
	for chan in range(int(discardLength / 2), bandpass.shape[0] - discardLength):
		flagged = bandpass[chan] > testVal[chan - discardLength] + std * stDev[chan - discardLength]
		if zapChans[chan] or flagged:
			nearestVal = chan - chan % chanGroup
			nextVal = chan + (chanGroup - chan % chanGroup)
			bandpass[nearestVal: nextVal] = bandpass[nearestVal - chanGroup: nextVal - chanGroup]
			zapChans[nearestVal: nextVal] = 1.

	zapChansLoc = np.argwhere(zapChans)

	return f"{' -zap_chans '.join([''] + [' '.join([str(ele[0]), str(ele[-1])]) if len(ele) > 1 else str(ele) + ' ' + str(ele) for ele in grouping(zapChansLoc)])}"


roundDown = lambda x, y: y * int(x / y)
roundUp = lambda x, y: y * int((x + y) / y)
def generateHeimdallCmds(inputFils, inputDigifilFils, relPaths, sources, args, heimdallConfig = None, suffix = 'cands'):
	heimdallCmds = []
	heimdallDirs = []
	
	if inputDigifilFils is None:
		inputDigifilFils = inputFils

	for fil, digifil, rel, source in zip(inputFils, inputDigifilFils, relPaths, sources):

		try:
			if source in alias.keys():
				source = alias[source]
			dm = Pulsar(source)['dm']
		except Exception:
			if len(dmDict) == 0:
				with open(os.path.join(args.hdrs, "dmFallback.txt"), 'r') as ref:
					dms = ref.readlines()
					for line in dms:
						filSource, dm = line.split('\t')
						dmDict[filSource] = float(dm)

			dm = dmDict[source]
		
		dm = float(dm)


		if heimdallConfig is None:
			dm0, dm1, dm_tol = max(3, roundDown(max(dm * 0.6, dm - 15), 5)), roundUp(min(dm * 1.4, dm + 20), 5), 1.005
		else:
			dm0, dm1, dm_tol = heimdallConfig

		bandpassProfile = []
		for loc in np.linspace(0., 0.97, 12):
			spr = spp.FilReader(fil)
			bandpassProfile.append(spr.bandpass(start = int(spr.header.nsamples * loc), nsamps = int(0.01 * spr.header.nsamples)))
		bandpassProfile = np.max(bandpassProfile, axis = 0)

		rfiFlags = rfiZapping(bandpassProfile, zappedChans = np.arange(3700, 3904), gui = False, chanGroup = 8, windowSize = 16, std = 3., bandpassPassed = True)

		outputPrefix = outputPath(digifil, rel, source, args)
		heimdallDirs.append(f"{outputPrefix}_{suffix}")
		heimdallCmds.append(f"mkdir -p {outputPrefix}_{suffix}/\nheimdall -f {digifil} -output_dir {heimdallDirs[-1]} -dm {dm0} {dm1} -dm_tol {dm_tol} {args.heim_args} {rfiFlags}\n")
		
	return heimdallDirs, heimdallCmds



def generateCandidateCmds(inputFils, heimdallDirs, sources, args):
	candCmds = []

	for fil, rel, source, heimdallCand in zip(inputFils, relPaths, sources, heimdallDirs):
		outputPrefix = outputPath(fil, rel, source, args)
		candCmds.append(f"heimdallPulseExtraction.py -i {fil} -f {heimdallCand} -o {outputPrefix}_candPlots {args.cand_args}")

	return candCmds


"""
def generateCleanupCmds()

"""



heimdallDefaults = '-nsamps_gulp 500000 -V -no_scrunching'
heimdallConfig = [5, 500, 1.01]
plotDefaults = '--deci 16 --samples 76800 --plot_deci_norm'
iqrmDefaults = '-t 5.5 -m 32 -s 8192'
candDefaults = '-r -p -q -b 6 -t -s 7.5 -k'


if __name__ == '__main__':
	parser = argparse.ArgumentParser(description = "Process all raw UDP files in a folder structure with CDMT.")

	parser.add_argument('-i', dest = 'input', default = './', help = "Folder to search")
	parser.add_argument('-p', dest = 'port', default = '16130', help = "Reference port number in file name")
	parser.add_argument('-m', dest = 'hdrs', default = '/mnt/ucc4_data2/data/David/hdrs/mode5/', help = "Folder of Sigproc header files")
	parser.add_argument('-s', dest = 'structure', default = False, action = 'store_true', help = "Keep input folder structure rather than outputting all files to the same output folder.")
	parser.add_argument('-o', dest = 'output', default = './', help = "Output folder location")
	parser.add_argument('-n', dest = 'nodes', default = 1, help = "Number of output files to generate (number of separate compute nodes)")
	parser.add_argument('-b', dest = 'deci', default = 16, help = "Decimation factor")
	
	parser.add_argument('--heimdall_args', dest = 'heim_args', default = heimdallDefaults, help = f"Default parameters to pass to Heimdall (default: '{heimdallDefaults}')")
	parser.add_argument('--heimdall_config', dest = 'heim_conf', default = heimdallConfig, type = float, nargs = 3, help = "Heimdall parameters for full scan [dm0, dm1, dm_tol]")
	#parser.add_argument('--iqrm_args', dest = 'iqrm_args', default = iqrmDefaults, help = f"Default parameters to pass to IQRM (default: '{iqrmDefaults}')")
	#parser.add_argument('--plot_args', dest = 'plot_args', default = plotDefaults, help = f"Default parameters to pass to filQuickPlot.py (default: '{plotDefaults}')")
	#parser.add_argument('--cand_args', dest = 'cand_args', default = candDefaults, help = f"Default parameters to pass to heimdallPulseExtraction.py (default: '{candDefaults}'")

	parser.add_argument('--heimdall', dest = 'heimdall', default = False, action = 'store_true', help = "Enable Heimdall search on the output.")
	parser.add_argument('--disable_heimdall_fullscan', dest = 'heimdall_full', default = True, action = 'store_false', help = "(If Heimdall isn't disabled) Disable a scan over the maximum DM range")
	#parser.add_argument('--disable_iqrm', dest = 'iqrm', default = True, action = 'store_false', help = "Disable running IQRM on the datasets")
	#parser.add_argument('--disable_plot', dest = 'plot', default = True, action = 'store_false', help = "Disable plotting the filterbank")
	#parser.add_argument('--disable_cleanup_prompt', dest = 'cleanup_prompt', default = True, action = 'store_false', help = "Disable prompt prior to removing artefacts.")
	#parser.add_argument('--disable_cleanup', dest = 'cleanup', default = True, action = 'store_false', help = "Disable cleaning up artefacts")
	parser.add_argument('--disable_cand_prompt', dest = 'cand_prompt', default = True, action = 'store_false', help = "(If Heimdall isn't disabled) Disable prompting for intesting candidates to extract")
	parser.add_argument('--extra', dest = 'extra', type = str, default = None, help = "Suffix on the end of a file")
	args = parser.parse_args()

	rawUdps, relRawPath = exploreFolderTree(args.input, 'zst', args.port)
	print("Init")
	outputPath = f"{args.output}/cdmtProc{'_' + args.extra if not isinstance(args.extra, type(None)) else ''}.sh"
	if os.path.exists(outputPath):
		raise RuntimeError(f"Output file already exists at {outputPath}, exiting.")

	sources = [folderName.split('/')[-2][14:].split('_')[0] for folderName in rawUdps]
	sourceDel = []
	mockHdr = []
	for idx, source in enumerate(sources):
		print(source)
		if not os.path.exists(os.path.join(args.hdrs, source + ".sigprochdr")):
			try:
				psr = Pulsar(source)
				mockHdr.append(f"mockHeader -tel 1916 -mach 1916 -source {source} -ra {psr['raj']} -dec {psr['decj']} -tsamp 0.00000512 -nbits 8 -fch1 197.558594 -fo -0.1953125 -nchans 488 {source}.sigprochdr\n")
			except:
				print(f"Unable to find header for source {source} in folder at {args.hdrs}, passing.")
				sourceDel.append(idx)

	for idx in reversed(sourceDel):
		del sources[idx]
		del rawUdps[idx]
		del relRawPath[idx]

	print("cdmt")
	cdmtCmds, cdmtFils = generateCDMTCmds(rawUdps, relRawPath, sources, args)
	print("digi")
	digifilCmds, digifilFils = generateDigifilCmds(cdmtFils, args)

	print("write")
	with open(outputPath, 'w') as outRef:
		if len(mockHdr) > 0:
			outRef.writelines(mockHdr)
			outRef.writelines("\n\n\n")

		outRef.writelines(cdmtCmds)
		outRef.writelines("\n\n\n")

		outRef.writelines(digifilCmds)
		outRef.writelines(["\nchmod o+r ./*.fil\n\n\n"])

		print("heimdall")
		if args.heimdall:
			heimdallDirs, heimdallCmds = generateHeimdallCmds(cdmtFils, digifilFils, relRawPath, sources, args, suffix = 'cands')
			outRef.writelines("\n\n\n")
			outRef.writelines(heimdallCmds)

			if args.cand_prompt:
				candsCmds = generateCandidateCmds(digifilFils, heimdallDirs, sources, args)
				outRef.writelines("\n\n\n")
				outRef.writelines(candsCmds)
		print("full")
		if args.heimdall and args.heimdall_full:
			heimdallFullDirs, heimdallFullCmds = generateHeimdallCmds(cdmtFils, digifilFils, relRawPath, sources, args, heimdallConfig = heim_conf, suffix = 'full_cands')
			outRef.writelines("\n\n\n")
			outRef.writelines(heimdallFullCmds)

			if args.cand_prompt:
				candsFullCmds = generateCandidateCmds(digifilFils, heimdallFullDirs, sources, args)
				outRef.writelines("\n\n\n")
				outRef.writelines(candsFullCmds)
		outRef.writelines("\n\n\nchown -R 1000:1000 .")


	print(f"Finished for {len(cdmtCmds)}, output file at {outputPath}, exiting.")



