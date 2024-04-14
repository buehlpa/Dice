import random
import os
import pandas as pd
from scipy.stats import chisquare

from utils.argparser import load_and_parse_args

from io import BytesIO
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
import matplotlib.pyplot as plt
import matplotlib# lock matqplotlib for multithreading
from matplotlib.ticker import MaxNLocator

matplotlib.use('Agg') 
from threading import Lock
matplotlib_lock = Lock()


#load arguments from configuration file
# on windows : r'C:\Users\buehl\repos\Dice\rasperry_run\configuration\config_win.json'


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



def place_image(ax, img_path, xy, zoom=1):
    img = plt.imread(img_path)
    imagebox = OffsetImage(img, zoom=zoom)
    ab = AnnotationBbox(imagebox, xy, frameon=True, xybox=(20, -15), boxcoords="offset points", pad=0)
    ax.add_artist(ab)

def plot_histogram(data_path, column_names=['white', 'red']):
    
    german_dict= {'white':'Weiss - Gewürfelt', 'red':'Rot - Gewürfelt'}
    with matplotlib_lock:
        df = pd.read_csv(data_path)
        fig, ax = plt.subplots(figsize=(12, 6))  # Adjust the figure size here
        
        # Set x-axis to integers only
        ax.xaxis.set_major_locator(MaxNLocator(integer=True))
        
        # Plot each column's histogram side by side
        bar_width = 0.25
        for i, column_name in enumerate(column_names):
            rolls = df[column_name].dropna().tolist()
            if len(rolls) != 0:
                # Calculate observed frequencies and p-value
                observed_frequencies = [rolls.count(i) / len(rolls) for i in range(1, 7)]
                
                # Plot bar chart for observed frequencies
                ax.bar([x + i * bar_width for x in range(1, 7)], 
                       observed_frequencies, 
                       alpha=0.8, label=german_dict[column_name], width=bar_width,
                       edgecolor='black',
                       color='red' if column_name == 'red' else 'white')
                
                # Annotate each bar with the actual count for each outcome
                for x, freq in zip(range(1, 7), observed_frequencies):
                    ax.text(x + (i * bar_width), freq + 0.0, f'{rolls.count(x)}', ha='center', va='bottom')

        # Plot theoretical probabilities (shared between both columns)
        theoretical_probs = [1/6] * 6
        ax.bar([x + len(column_names) * bar_width for x in range(1, 7)], 
               theoretical_probs, 
               alpha=0.5, label=f'Theoretisch', width=bar_width,
               color='blue', hatch='//')

        # Remove numerical x-tick labels and place images instead
        ax.set_xticks([1 + i * bar_width + len(column_names) * bar_width / 2 for i in range(6)])
        ax.set_xticklabels([])  # Remove x-tick labels
        ax.tick_params(axis='both', which='both', length=0)  # Remove axis ticks

        for i in range(1, 7):
            place_image(ax, os.path.join(args.STATPATH, f'side{i}.jpg'), xy=(i, 0), zoom=0.04)
            
        len_white = len(df['white'].dropna().tolist())
        len_red = len(df['red'].dropna().tolist())
        
        plt.title(f' Anzahl Würfe - Rot: {len_white}, Weiss: {len_red}')
        plt.ylabel('Relative Häufigkeit')
        plt.legend()
        #plt.show()
        
        
        img = BytesIO()
        plt.savefig(img, format='png')
        img.seek(0)
        plt.close()
        return img


