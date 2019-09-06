#!/usr/bin/env python

from __future__ import print_function

import fastjet as fj
import fjcontrib
import fjext

import tqdm
import argparse
import os
import sys
import numpy as np
import array 

import pyhepmc_ng
import ROOT

# Prevent ROOT from stealing focus when plotting
ROOT.gROOT.SetBatch(True)

#--------------------------------------------------------------
def logbins(xmin, xmax, nbins):
        lspace = np.logspace(np.log10(xmin), np.log10(xmax), nbins+1)
        arr = array.array('f', lspace)
        return arr

#--------------------------------------------------------------
def main():
  parser = argparse.ArgumentParser(description='jetscape in python', \
                                   prog=os.path.basename(__file__))
  parser.add_argument('-i', '--input', help='input file', \
                      default='low', type=str, required=True)
  parser.add_argument('--nev', help='number of events', \
                      default=1000, type=int)
  args = parser.parse_args()	

  # Use pyhepmc_ng to parse the HepMC file
  input_hepmc = pyhepmc_ng.ReaderAscii(args.input)
  if input_hepmc.failed():
    print ("[error] unable to read from {}".format(args.input))
    sys.exit(1)

  # Create a histogram with ROOT
  lbins = logbins(1., 500, 50)
  hJetPt04 = ROOT.TH1D("hJetPt04", "hJetPt04", 50, lbins)

  # jet finder
  fj.ClusterSequence.print_banner()
  print()
  jet_R0 = 0.4
  jet_def = fj.JetDefinition(fj.antikt_algorithm, jet_R0)
  jet_selector = fj.SelectorPtMin(50.0) & fj.SelectorPtMax(200.0) & fj.SelectorAbsEtaMax(3)

  # Loop through events
  all_jets = []
  event_hepmc = pyhepmc_ng.GenEvent()
  pbar = tqdm.tqdm(range(args.nev))
  while not input_hepmc.failed():
    ev = input_hepmc.read_event(event_hepmc)
    if input_hepmc.failed():
      nstop = pbar.n
      pbar.close()
      print('End of HepMC file at event {} '.format(nstop))
      break
    jets_hepmc = find_jets_hepmc(jet_def, jet_selector, event_hepmc)
    all_jets.extend(jets_hepmc)
    pbar.update()

    # Fill histogram
    [fill_jet_histogram(hJetPt04, jet) for jet in all_jets]
    
    if pbar.n >= args.nev:
      pbar.close()
      print('{} event limit reached'.format(args.nev))
      break

  # Plot and save histogram
  print('Creating ROOT file...')
  c = ROOT.TCanvas('c', 'c', 600, 450)
  c.cd()
  c.SetLogy()
  hJetPt04.SetMarkerStyle(21)
  hJetPt04.Sumw2()
  hJetPt04.Draw('E P')
  output_filename = './AnalysisResult.root'
  c.SaveAs(output_filename)

  fout = ROOT.TFile(output_filename, "update")
  fout.cd()
  hJetPt04.Write()
  fout.Close()
  
#--------------------------------------------------------------
def find_jets_hepmc(jet_def, jet_selector, hepmc_event):

  fjparts = []
  hadrons = []
  for vertex in hepmc_event.vertices:
    vertex_time = vertex.position.t
    if abs(vertex_time - 100) < 1e-3:
      hadrons = vertex.particles_out

  for hadron in hadrons:
    psj = fj.PseudoJet(hadron.momentum.px, hadron.momentum.py, hadron.momentum.pz, hadron.momentum.e)
    fjparts.append(psj)

  jets = jet_selector(jet_def(fjparts))
  return jets

#--------------------------------------------------------------
def fill_jet_histogram(hist, jet):
        hist.Fill(jet.perp())

#--------------------------------------------------------------
if __name__ == '__main__':
	main()
