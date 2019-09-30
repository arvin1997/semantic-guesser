"""
Created on Feb 24, 2012

@author: 100457636
"""


class TagsetConverter():

    def __init__(self):
        self._claws_brown_map = {
            'APPGE': 'PP$$',
            'AT': 'AT',
            'AT1': 'AT',
            # 'BCL' : '',
            'CC': 'CC',
            'CCB': 'CC',
            'CS': 'CS',
            'CSA': 'CS',
            'CSN': 'CS',
            'CST': 'CS',
            'CSW': 'CS',
            'DA': 'AP',
            'DA1': 'AP',
            'DA2': 'AP',
            'DAR': 'AP',
            'DAT': 'AP',
            'DB': 'ABN',
            'DB2': 'ABX',
            'DD': 'DTI',
            'DT1': 'DT',
            'DD2': 'DTS',
            'DDQ': 'WDT',
            'DDQGE': 'WP$',
            'DDQV': 'WDT',
            'EX': 'EX',
            # 'FO' : '',
            # 'FU' : '',
            'FW': 'FW',  # abusing the Brown notation
            # 'GE' : '',
            'IF': 'IN',
            'II': 'IN',
            'IO': 'IN',
            'IW': 'IN',
            'JJ': 'JJ',
            'JJR': 'JJR',
            'JJT': 'JJT',
            'JK': 'JJ',
            'MC': 'CD',
            'MC1': 'CD',
            'MC2': 'CD',
            'MCGE': 'CD$',
            'MCMC': 'CD',
            'MD': 'OD',
            'MF': 'CD',
            'ND1': 'NR',
            'NN': 'NN',
            'NN1': 'NN',
            'NN2': 'NNS',
            'NNA': 'NN',
            'NNB': 'NN',
            'NNL1': 'NN',
            'NNL2': 'NNS',
            'NNO': 'NN',
            'NNO2': 'NNS',
            'NNT1': 'NN',
            'NNT2': 'NNS',
            'NNU': 'NN',
            'NNU1': 'NN',
            'NNU2': 'NNS',
            'NP': 'NP',
            'NP1': 'NP',
            'NP2': 'NPS',
            'NPD1': 'NR',
            'NPD2': 'NRS',
            'NPM1': 'NP',
            'NPM2': 'NPS',
            'PN': 'PN',
            'PN1': 'PN',
            'PNQO': 'WPO',
            'PNQS': 'WPO',
            'PNQV': 'WPS',
            'PNX1': 'PPL',
            'PPGE': 'PP$$',
            'PPH1': 'PPS',
            'PPHO1': 'PPO',
            'PPHO2': 'PPO',
            'PPHS1': 'PPS',
            'PPHS2': 'PPSS',
            'PPIO1': 'PPO',
            'PPIO2': 'PPO',
            'PPIS1': 'PPSS',
            'PPIS2': 'PPSS',
            'PPX1': 'PPL',
            'PPX2': 'PPLS',
            'PPY': 'PPO',
            'RA': 'RB',
            'REX': 'RB',
            'RG': 'QL',
            'RGQ': 'QL',
            'RGR': 'RBR',
            'RGT': 'RBT',
            'RL': 'RB',
            'RP': 'RP',
            'RPK': 'RP',
            'RR': 'RB',
            'RRQ': 'WRB',
            'RRQV': 'WRB',
            'RRR': 'RBR',
            'RRT': 'RBT',
            'RT': 'NR',
            'TO': 'TO',
            'UH': 'UH',
            'VB0': 'BE',
            'VBDR': 'BED',
            'VBDZ': 'BEDZ',
            'VBG': 'BEG',
            'VBI': 'BE',
            'VBM': 'BEM',
            'VBN': 'BEN',
            'VBR': 'BER',
            'VBZ': 'BEZ',
            'VD0': 'DO',
            'VDD': 'DOD',
            'VDG': 'VBG',
            'VDI': 'DO',
            'VDN': 'DOD',
            'VDZ': 'DOZ',
            'VH0': 'HV',
            'VHD': 'HVD',
            'VHG': 'HVG',
            'VHI': 'HV',
            'VHN': 'HVN',
            'VHZ': 'HVZ',
            'VM': 'MD',
            'VMK': 'MD',
            'VV0': 'VB',
            'VVD': 'VBD',
            'VVG': 'VBG',
            'VVGK': 'VBG',
            'VVI': 'VB',
            'VVN': 'VBN',
            'VVNK': 'VBN',
            'VVZ': 'VBZ',
            'XX': '*'
            # 'ZZ1' : '',
            # 'ZZ2' : ''
        }

        # need to review this, especially the pronouns part
        self.brownToClaws7 = {'ABL': 'RG',  # ~
                              'ABN': 'DB',
                              'ABX': 'DA2',
                              'AP': 'DA',  # ~
                              'AP$': 'AP',  # ~
                              'AP+AP': 'AP',  # ~
                              'AT': 'AT',
                              'BE': 'VBI',
                              'BED': 'VBDR',
                              'BED*': 'VBDR',  # ~
                              'BEDZ': 'VBDZ',
                              'BEDZ*': 'VBDZ',  # ~
                              'BEG': 'VBG',
                              'BEM': 'VBM',
                              'BEM*': 'VBM',  # ~
                              'BEN': 'VBN',
                              'BER': 'VBR',
                              'BER*': 'VBR',  # ~
                              'BEZ': 'VBZ',
                              'BEZ*': 'VBZ',  # ~
                              'CC': 'CC',
                              'CD': 'MC',
                              'CD$': 'MCGE',
                              'CS': 'CS',
                              'DO': 'VD0',
                              'DO*': 'VD0',  # ~
                              'DO+PPSS': 'VD0',  # ~
                              'DOD': 'VDD',
                              'DOD*': 'VDD',  # ~
                              'DOZ': 'VDZ',
                              'DOZ*': 'VDZ',  # ~
                              'DT': 'DD1',
                              'DT$': None,  # ~
                              'DT-BEZ': 'DD1',  # ~
                              'DT-MD': 'DD1',  # ~
                              'DTI': 'DD',
                              'DTS': 'DT2',
                              'DTS+BEZ': 'DT2',  # ~
                              'DTX': 'DD1',  # ~
                              'EX': 'EX',
                              'EX-BEZ': 'EX',  # ~
                              'EX-HDV': 'EX',  # ~
                              'EX-MD': 'EX',  # ~
                              'FW-*': 'FW',
                              'FW-AT': 'FW',
                              'FW-AT+NN': 'FW',
                              'FW-AT+NP': 'FW',
                              'FW-BE': 'FW',
                              'FW-BER': 'FW',
                              'FW-BEZ': 'FW',
                              'FW-CC': 'FW',
                              'FW-CD': 'FW',
                              'FW-CS': 'FW',
                              'FW-DT': 'FW',
                              'FW-BER+BEZ': 'FW',
                              'FW-DTS': 'FW',
                              'FW-HV': 'FW',
                              'FW-IN': 'FW',
                              'FW-IN+AT': 'FW',
                              'FW-IN+NN': 'FW',
                              'FW-IN+NP': 'FW',
                              'FW-JJ': 'FW',
                              'FW-JJR': 'FW',
                              'FW-JJT': 'FW',
                              'FW-NN': 'FW',
                              'FW-NN$': 'FW',
                              'FW-NNS': 'FW',
                              'FW-NP': 'FW',
                              'FW-NPS': 'FW',
                              'FW-NR': 'FW',
                              'FW-OD': 'FW',
                              'FW-PN': 'FW',
                              'FW-PP$': 'FW',
                              'FW-PPL': 'FW',
                              'FW-PPL+VBZ': 'FW',
                              'FW-PPO': 'FW',
                              'FW-PPO+IN': 'FW',
                              'FW-PPS': 'FW',
                              'FW-PPSS': 'FW',
                              'FW-PPSS+HV': 'FW',
                              'FW-QL': 'FW',
                              'FW-RB': 'FW',
                              'FW-RB+CC': 'FW',
                              'FW-TO+VB': 'FW',
                              'FW-UH': 'FW',
                              'FW-VB': 'FW',
                              'FW-VBD': 'FW',
                              'FW-VBG': 'FW',
                              'FW-VBN': 'FW',
                              'FW-VBZ': 'FW',
                              'FW-WDT': 'FW',
                              'FW-WPO': 'FW',
                              'FW-WPS': 'FW',
                              'HV': 'VH0',
                              'HV*': 'VH0',
                              'HV+TO': None,
                              'HVD': 'VHD',
                              'HVD*': 'VHD',
                              'HVG': 'VHG',
                              'HVN': 'VHN',
                              'HVZ': 'VHZ',
                              'MD': 'VM',
                              'MD*': 'VM',
                              'MD+HV': 'VM',
                              'MD+PPSS': 'VM',
                              'MD+TO': 'VM',
                              'NN': 'NN1',
                              'NN$': 'NN1',
                              'NN+BEZ': 'NN1',
                              'NN+HVD': 'NN1',
                              'NN+HVZ': 'NN1',
                              'NN+IN': 'NN1',
                              'NN+MD': 'NN1',
                              'NN+NN': 'NN1',
                              'NNS': 'NN2',
                              'NNS$': 'NN2',
                              'NNS+MD': 'NN2',
                              'NP': 'NP1',
                              'NP$': 'NP1',
                              'NP+BEZ': 'NP1',
                              'NP+HVZ': 'NP1',
                              'NP+MD': 'NP1',
                              'NPS': 'NP2',
                              'NPS$': 'NP2',
                              'NR': 'NN',
                              'NR$': 'NN',
                              'NR+MD': 'NN',
                              'NRS': 'NN',
                              'OD': 'MD',
                              'PN': 'PN',
                              'PN$': 'PN',
                              'PN+BEZ': 'PN',
                              'PN+HVD': 'PN',
                              'PN+HVZ': 'PN',
                              'PN+MD': 'PN',
                              'PP$': 'APPGE',
                              'PP$$': 'PPGE',
                              'PPL': 'PPX1',
                              'PPLS': 'PPX2',
                              'QL': 'RG',
                              'QLP': 'RR',
                              'RB': 'RR',
                              'RB$': 'RR',
                              'RB+BEZ': 'RR',
                              'RB+CS': 'RR',
                              'RBR': 'RRR',
                              'RBR+CS': 'RRR',
                              'RBT': 'RRT',
                              'RN': 'RR',
                              'RP': 'RP',
                              'RP+IN': 'RP',
                              'TO': 'TO',
                              'TO+VB': 'TO',
                              'UH': 'UH',
                              'VB': 'VV0',
                              'VB+AT': 'VV0',
                              'VB+IN': 'VV0',
                              'VB+JJ': 'VV0',
                              'VB+PPO': 'VV0',
                              'VB+RP': 'VV0',
                              'VB+TO': 'VV0',
                              'VB+VP': 'VV0',
                              'VBD': 'VVD',
                              'VBG': 'VVG',
                              'VBG+TO': 'VVG',
                              'VBZ': 'VVZ',
                              'WDT': 'DDQ',
                              'WDT+BER': 'DDQ',
                              'WDT+BER+PP': 'DDQ',
                              'WDT+BEZ': 'DDQ',
                              'WDT+DO+PPS': 'DDQ',
                              'WDT+DOD': 'DDQ',
                              'WDT+HVZ': 'DDQ',
                              'WP$': 'DDQGE',
                              'WPO': 'PNQS',
                              'WPS': 'DDQV',
                              'WPS+BEZ': 'DDQV',
                              'WPS+HVD': 'DDQV',
                              'WPS+HVZ': 'DDQV',
                              'WPS+MD': 'DDQV',
                              'WQL': 'RGQV',
                              'WRB': 'RRQ',
                              'WRB+BER': 'RRQ',
                              'WRB+BEZ': 'RRQ',
                              'WRB+DO': 'RRQ',
                              'WRB+DOD': 'RRQ',
                              'WRB+DOD*': 'RRQ',
                              'WRB+DOZ': 'RRQ',
                              'WRB+IN': 'RRQ',
                              'WRB+MD': 'RRQ'
                              }

    def brownToClaws7(self, tag, word):
        # should treat pronouns based on word here,
        # since the mapping between tags is very imperfect
        pass

    def claws7ToBrown(self, tag):
        t = tag.upper()
        return self._claws_brown_map[t] if t in self._claws_brown_map else None

    def brownToWordNet(self, tag):
        tag = tag.lower()
        l = tag[0]  # first letter
        ll = tag[:2]  # two first letters
        if ll == 'np':
            return None
        elif l == 'n':
            return 'n'
        elif l in ('b', 'v', 'h') or ll == 'do':
            return 'v'
        elif l in ('r') or ll == 'wr':
            return 'r'
        elif l == 'j':
            return 'a'
        else:
            return None

    def clawsToWordNet(self, tag):
        tag = tag.lower()
        l = tag[0]  # first letter
        ll = tag[:2]  # two first letters
        if ll == 'np':
            return 'n'
        elif l == 'n':
            return 'n'
        elif l == 'v':
            return 'v'
        elif l == 'r':
            return 'r'
        elif l == 'j':
            return 'a'
        else:
            return None
