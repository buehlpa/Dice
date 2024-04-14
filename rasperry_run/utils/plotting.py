import random
import os
import pandas as pd
from scipy.stats import chisquare

from utils.argparser import load_and_parse_args

from io import BytesIO
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
import matplotlib.pyplot as plt
import matplotlib# lock matqplotlib for multithreading
matplotlib.use('Agg') 
from threading import Lock
matplotlib_lock = Lock()




#load arguments from configuration file
# on windows : r'C:\Users\buehl\repos\Dice\rasperry_run\configuration\config_win.json'
# lin: 'configuration/config.json'

#argpath=r'C:\Users\buehl\repos\Dice\rasperry_run\configuration\config_win.json' #
argpath='configuration/config.json'
global args 
args=load_and_parse_args(argpath)



def append_to_csv(filepath, new_df):
    existing_df = pd.read_csv(filepath)
    updated_df = pd.concat([existing_df, new_df], ignore_index=True)
    updated_df.to_csv(filepath, index=False)

def check_empty_dice_results(filepath):
    df = pd.read_csv(filepath)
    if df.empty:
        return True
    else:
        return False

def create_dataframe_fillNA(data:dict):
    ''' Create a DataFrame from a dictionary and fill missing values with NaN'''
    max_length = max(len(values) for values in data.values())
    for key, values in data.items():
        data[key] = values + [None] * (max_length - len(values))
    return pd.DataFrame(data)

def dummy_dice_pred():
    dice_dict = {"white": [], "red": []}
    
    for color in dice_dict:
        num_numbers = 1 #random.randint(0, 5)  # Randomly select the number of numbers to add
        numbers = [random.randint(1, 6) for _ in range(num_numbers)]  # Generate random numbers
        dice_dict[color] = numbers
    
    return dice_dict , True

def write_result(dice_prediction, filepath='results/results.csv'):
    dice_dict, dice_pass = dice_prediction
    
    if not dice_pass:
        dice_msg="Dice: Prediction failed, try again!"

    else:
        print('in else')
        if check_empty_dice_results(filepath):
            throw_number=0
            print("First throw")
        else:
            print(dice_dict)
            df = pd.read_csv(filepath)
            throw_number=df['throw'].iloc[-1]
            print(throw_number)
            
        throw_number += 1
        dice_dict_NA=create_dataframe_fillNA(dice_dict)
        dice_dict_NA['throw'] = [throw_number] * len(dice_dict['white'])
        append_to_csv(filepath, dice_dict_NA)
        dice_msg="Dice: "+str(dice_dict)
        
    return dice_msg 




##### Histograms

# helper function to place image on histogarmmplot
def place_image(ax, img_path, xy, zoom=1):
    # Load the image
    img = plt.imread(img_path)
    # Create an OffsetImage
    imagebox = OffsetImage(img, zoom=zoom)
    # Create an AnnotationBbox
    ab = AnnotationBbox(imagebox, xy, frameon=True, xybox=(10, -15), boxcoords="offset points", pad=0)
    # Add it to the axes
    ax.add_artist(ab)



# plot histogram
def plot_histogram(data_path, column_name):
    
    '''read data from csv file and plot histogram of the column_name with annotated dices on x-axis'''
    
    with matplotlib_lock:
        df = pd.read_csv(data_path)

        rolls=df[column_name].dropna().tolist()
        # Theoretical distribution for a fair dice (uniform distribution)
        fair_probs = [1/6] * 6  # Since each outcome (1-6) has an equal probability
        
        p_value=0
        if len(rolls) != 0:
            # Counting the frequency of each outcome for the unfair dice
            unfair_probs = [rolls.count(i) / len(rolls) for i in range(1, 7)]
            observed_frequencies = [rolls.count(i) for i in range(1, 7)]
            expected_frequencies = [len(rolls) / 6] * 6
            chi_squared_stat, p_value = chisquare(observed_frequencies, f_exp=expected_frequencies)
        
        # Create the plot
        fig, ax = plt.subplots()

        # Plotting the bar charts
        ax.bar(range(1, 7), fair_probs, alpha=1, color='#0165A8', label='Theoretisch', width=0.4)
        
        if len(rolls) != 0 and column_name == 'red':
            ax.bar([x + 0.4 for x in range(1, 7)], unfair_probs, alpha=0.8, color='red', label='Gewürfelt', width=0.4)
        elif len(rolls) != 0 and column_name == 'white':
            ax.bar([x + 0.4 for x in range(1, 7)], unfair_probs, alpha=0.8, edgecolor='black', color='white', label='Gewürfelt', width=0.4)

        # Remove numerical x-tick labels and place images instead
        ax.set_xticks(range(1, 7))
        ax.set_xticklabels([])  # Remove x-tick labels
        ax.tick_params(axis='both', which='both', length=0)  # Remove axis ticks

        for i in range(1, 7):
            place_image(ax, os.path.join(args.STATPATH, f'side{i}.jpg'), xy=(i, 0), zoom=0.04)
            
        plt.title(f'Häufigkeiten von Würfelergebnissen, Anzahl Würfe: {len(rolls)} p= {p_value:.3f}')
        plt.legend()
        #plt.xlabel('Würfel Augen', labelpad=30)
        plt.ylabel('Relative Häufigkeit')
                

        img = BytesIO()
        plt.savefig(img, format='png')
        img.seek(0)
        plt.close()
        return img


class PlotGenerator:
    def __init__(self, data_path, column_name):
        self.data_path = data_path
        self.column_name = column_name
        self.matplotlib_lock = Lock()
        
    @staticmethod
    def place_image(ax, img_path, xy, zoom=1):
        # Load the image
        img = plt.imread(img_path)
        # Create an OffsetImage
        imagebox = OffsetImage(img, zoom=zoom)
        # Create an AnnotationBbox
        ab = AnnotationBbox(imagebox, xy, frameon=True, xybox=(10, -15), boxcoords="offset points", pad=0)
        # Add it to the axes
        ax.add_artist(ab)
    
    def plot_histogram(self):
        '''read data from csv file and plot histogram of the column_name with annotated dices on x-axis'''
        #with self.matplotlib_lock:
        df = pd.read_csv(self.data_path)

        rolls = df[self.column_name].dropna().tolist()
        # Theoretical distribution for a fair dice (uniform distribution)
        fair_probs = [1/6] * 6  # Since each outcome (1-6) has an equal probability
        
        p_value = 0
        if len(rolls) != 0:
            # Counting the frequency of each outcome for the unfair dice
            unfair_probs = [rolls.count(i) / len(rolls) for i in range(1, 7)]
            observed_frequencies = [rolls.count(i) for i in range(1, 7)]
            expected_frequencies = [len(rolls) / 6] * 6
            chi_squared_stat, p_value = chisquare(observed_frequencies, f_exp=expected_frequencies)
        
        # Create the plot
        fig, ax = plt.subplots()

        # Plotting the bar charts
        ax.bar(range(1, 7), fair_probs, alpha=1, color='#0165A8', label='Theoretisch', width=0.4)
        
        if len(rolls) != 0 and self.column_name == 'red':
            ax.bar([x + 0.4 for x in range(1, 7)], unfair_probs, alpha=0.8, color='red', label='Gewürfelt', width=0.4)
        elif len(rolls) != 0 and self.column_name == 'white':
            ax.bar([x + 0.4 for x in range(1, 7)], unfair_probs, alpha=0.8, edgecolor='black', color='white', label='Gewürfelt', width=0.4)

        # Remove numerical x-tick labels and place images instead
        ax.set_xticks(range(1, 7))
        ax.set_xticklabels([])  # Remove x-tick labels
        ax.tick_params(axis='both', which='both', length=0)  # Remove axis ticks

        for i in range(1, 7):
            self.place_image(ax, os.path.join(args.STATPATH, f'side{i}.jpg'), xy=(i, 0), zoom=0.04)
            
        plt.title(f'Häufigkeiten von Würfelergebnissen, Anzahl Würfe: {len(rolls)} p= {p_value:.3f}')
        plt.legend()
        #plt.xlabel('Würfel Augen', labelpad=30)
        plt.ylabel('Relative Häufigkeit')
                

        img = BytesIO()
        plt.savefig(img, format='png')
        plt.close()
        img.seek(0)

        return img
