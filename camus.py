from ca import *
import random as rd
import music21 as m21 
from music21 import instrument
import csv

class GeneralConfiguration:
    def __init__(self, m21_instrument, real_range, max_interval, pitch_collection):
        self.instrument = m21_instrument
        self.max_interval = max_interval
        self.pitch_collection = pitch_collection
        self.real_range = real_range
    
    def choose_base_note(self):
        return rd.choice(self.pitch_collection.getPitches(self.real_range[0], self.real_range[1]))

    
    def and_coding(self, neighbours):
        w1 = neighbours[:4]
        w2 = w1[::-1]
        w3 = neighbours[4:]
        w4 = w3[::-1]

        tgg = tuple([int(i or j) for i,j in zip(w1,w2)])
        dur = tuple([int(i or j) for i,j in zip(w3,w4)])

        translation = {
            (0,0,0,0): [[0], [1,2]],
            (0,0,0,1): [[0,1,2]],
            (0,0,1,0): [[0], [2], [1]],
            (0,0,1,1): [[2],[1],[0]],
            (0,1,0,1): [[0],[1],[2]],
            (0,1,1,0): [[2],[0],[1]],
            (0,1,1,1): [[1],[0],[2]],
            (1,0,0,1): [[2],[0,1]],
            (1,0,1,1): [[1],[2],[0]],
            (1,1,1,1): [[1],[0,2]],
            (0,1,0,0): [[1,2], [0]],
            (1,0,0,0): [[0,2], [1]],
            (1,0,1,0): [[0,1], [2]],
            (1,1,0,0): [[0,1,2]],
            (1,1,0,1): [[0,1,2]],
            (1,1,1,0): [[0,1,2]]
        }

        return (translation[tgg], translation[dur])

    def and_to_durs(self, tgg_code, dur_code, offsets):
        trigger_offsets = {}
        durations = {}

        random_offsets = rd.choices(offsets[:-1], k=len(tgg_code))
        random_offsets.sort()
        random_release = rd.choices(offsets[offsets.index(random_offsets[-1])+1:], k=len(dur_code))
        random_release.sort()

        for pos,offset in enumerate(random_offsets):
            for element in tgg_code[pos]:
                trigger_offsets[element] = offset
                
        for pos,offset in enumerate(random_release):
            for element in dur_code[pos]:
                durations[element] = offset - trigger_offsets[element]
        
        return (trigger_offsets, durations)
    
    def generate_durs(self, neighbours, offsets, beats_per_measure=None):
        tgg_code, dur_code = self.and_coding(neighbours)
        return self.and_to_durs(tgg_code, dur_code, offsets)


class MelodicConfiguration(GeneralConfiguration):
    def __init__(self, m21_instrument, real_range, max_interval, pitch_collection):
        super().__init__(m21_instrument, real_range, max_interval, pitch_collection)
    
    def and_coding(self, neighbours):
        w1 = neighbours[:4]
        w2 = w1[::-1]

        tgg = tuple([int(i or j) for i,j in zip(w1,w2)])

        translation = {
            0: [0,1,2],
            1: [0,2,1],
            2: [1,2,0],
            3: [1,0,2],
            4: [2,0,1]
        }
        triggers = translation[sum(tgg)]
        return triggers
    
    def and_to_durs(self, tgg_code, offsets, beats_per_measure):
        trigger_offsets = {}
        durations = {}

        offsets_copy = [o for o in offsets]
        random_offsets = [offsets_copy.pop(rd.randint(0, len(offsets_copy)-2)) for i in range(len(tgg_code))]

        random_offsets.sort()
        releases = random_offsets[1:] + [beats_per_measure]

        for pos,offset in enumerate(random_offsets):
            trigger_offsets[tgg_code[pos]] = offset
            durations[tgg_code[pos]] = releases[pos] - offset
        
        return (trigger_offsets, durations)

    def generate_durs(self, neighbours, offsets, beats_per_measure):
        tgg_code = self.and_coding(neighbours)
        return self.and_to_durs(tgg_code, offsets, beats_per_measure)
    
class HarmonicConfiguration(GeneralConfiguration):
    def __init__(self, m21_instrument, real_range, max_interval, pitch_collection):
        super().__init__(m21_instrument, real_range, max_interval, pitch_collection)
    
    def generate_durs(self, neighbours, offsets, beats_per_measure):
        tgg_code = [0,1,2]
        return self.and_to_durs(tgg_code, offsets, beats_per_measure)
    
    def and_to_durs(self, tgg_code, offsets, beats_per_measure):
        trigger_offsets = {}
        durations = {}

        random_offset = offsets[rd.randint(0,len(offsets)-2)]
        release = beats_per_measure

        for e in tgg_code:
            trigger_offsets[e] = random_offset
            durations[e] = release - random_offset
        
        return (trigger_offsets, durations)


def camus(input_cells, multi_state_input_cells, boundaries, k=16,
            instruments=[m21.instrument.Piano(), m21.instrument.Guitar()],
            offsets=[0,1,2,3,4],
            time_signature='4/4'):

    #criando os autômatos que serão utilizados
    gol_automata = GameOfLife(input_cells, boundaries, 1)
    dcs_automate = DemonCyclicSpace(multi_state_input_cells, 1, len(instruments))


    #criando as partes da peça de saída
    harmony = [stream.Part() for inst in instruments]

    [p.insert(0, m21.meter.TimeSignature(time_signature)) for p in harmony]

    #o autômato evolui dado o número de compassos de entrada
    i=0
    while i<k:

        #andando com o relógio em ambos os autômatos
        active_notes = [pair for row in gol_automata.apply_rules() for pair in row]
        active_instruments = dcs_automate.apply_rules()

        #variável para garantir que só um acorde será gerado por instrumento
        check_instruments = [False for i in range(len(instruments))]

        #Inserindo um novo compasso em cada parte
        for part in harmony:
            part.append(stream.Measure())

        #adicionando acordes para cada célula ativa no autômato (1 por instrumento)
        while len(active_notes)>0 and (False in check_instruments):
            row, col = active_notes.pop(rd.randint(0, len(active_notes)-1))
            instrument_state = active_instruments[row][col]
            instrument_configuration = instruments[instrument_state]

            #se o instrumento ainda não tiver sido utilizado neste compasso, insere
            if not(check_instruments[instrument_state]):
                base_note = instrument_configuration.choose_base_note()
                conversion_constant = instrument_configuration.max_interval/(len(active_instruments))
                middle_note = instrument_configuration.pitch_collection.next(base_note, stepSize=int(row*conversion_constant)+1)
                upper_note = instrument_configuration.pitch_collection.next(middle_note, stepSize=int(col*conversion_constant)+1)

                #sorteando momentos de ativação das notas e durações através do código AND
                trigger_offsets, durations = instrument_configuration.generate_durs(gol_automata.get_neighbours(row, col), offsets, int(time_signature.split('/')[0]))

                #Adicionando cada nota em vozes diferentes, para permitir articulações em momentos diferentes
                measure = harmony[instrument_state].measure(-1)
                for pos,pitch in enumerate([base_note, middle_note, upper_note]):
                    voice = m21.stream.Voice()
                    final_note = m21.note.Note(pitch, duration=m21.duration.Duration(durations[pos]))
                    voice.append(final_note)
                    final_note.offset = trigger_offsets[pos]
                    measure.insert(0, voice)

                check_instruments[instrument_state] = True

        #checando se há instrumentos sem acordes no presente compasso (e inserindo pausas caso haja)
        for j,checked in enumerate(check_instruments):
            if not checked:
                print('not checked', i, j)
                measure = harmony[j].measure(-1)
                voice = m21.stream.Voice()
                voice.append(m21.note.Rest(duration=m21.duration.Duration(int(time_signature.split('/')[0]))))
                measure.append(voice)
        i+=1  
    
    [harmony[ind].insert(0, config.instrument) for ind, config in enumerate(instruments)]
    return harmony


#----------------------------Gerando dados de entrada-----------------------

#Número de compassos e arquivo csv de entrada
tam = int(sys.argv[1]) if len(sys.argv)>1 else 16
input_file = 'inputs/'+(sys.argv[2] if len(sys.argv)>2 else "input.csv")

#leitura do csv
with open(input_file, newline="") as csv_file:
    reader = csv.reader(csv_file, delimiter=',', quotechar='|')
    instruments_input = [eval(row[-1]+'Configuration')(
                        eval('instrument.'+row[0]+'()'),
                        row[1].split(' '),
                        int(row[2]),
                        eval('m21.scale.'+row[3]+'(\"'+row[4]+'\")')) for row in reader]

#Fórmula de compasso
time_signature = sys.argv[3] if len(sys.argv)>3 else '4/4'
beats_per_measure = int(time_signature.split('/')[0])

#Gera possíveis offsets a partir de uma unidade amostral
basic_unit = 0.5
based_offsets = [basic_unit*i for i in range(int(beats_per_measure//basic_unit)+1)]

#Dimensão do autômato
gt_interval = max([inst.max_interval for inst in instruments_input])
n = gt_interval if gt_interval>=4 else 4

#Gera matrizes iniciais dos CA's aleatoriamente
chord_input_cells = [rd.choices([0,1], [70, 30], k=n) for i in range(n)]
instrument_input_cells = [rd.choices(range(len(instruments_input)), k=n) for i in range(n)]

#Executa a função principal
stream_parts = camus(chord_input_cells, instrument_input_cells, [1,3,2,2], 
                    k=tam, instruments=instruments_input, 
                    offsets=based_offsets, time_signature=time_signature)

s = m21.stream.Stream()
[s.insert(0,p) for p in stream_parts]
s.write('xml', 'outputs/'+sys.argv[2][:-4]+'.xml')
s.write('midi', 'outputs/'+sys.argv[2][:-4]+'.midi')