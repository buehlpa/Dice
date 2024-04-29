import random
import os
import pandas as pd
from scipy.stats import chisquare,binom
import numpy as np


from utils.argparser import load_and_parse_args

from io import BytesIO
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
import matplotlib.pyplot as plt
from matplotlib import gridspec

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
    '''dummy fucniton to simulate model'''
    dice_dict = {"white": [], "red": []}
    for color in dice_dict:
        num_numbers = 1 #random.randint(0, 5)  # Randomly select the number of numbers to add
        numbers = [random.randint(1, 6) for _ in range(num_numbers)]  # Generate random numbers
        dice_dict[color] = numbers
    return dice_dict , True

def write_result(dice_prediction, filepath='results/results.csv'):
    dice_dict, dice_pass = dice_prediction
    
    if not dice_pass:
        dice_msg="Vorhersage fehlerhaft, Bitte nochmals versuchen!"

    else:
        if check_empty_dice_results(filepath):
            throw_number=0
        else:
            df = pd.read_csv(filepath)
            throw_number=df['throw'].iloc[-1]
            
        throw_number += 1
        dice_dict_NA=create_dataframe_fillNA(dice_dict)
        dice_dict_NA['throw'] = [throw_number] * len(dice_dict['white'])
        append_to_csv(filepath, dice_dict_NA)
        dice_msg=convert_output(dice_dict)
        
    return dice_msg 

def convert_output(dice_dict):
    color_mapping = {
        "white": "WEISS",
        "red": "ROT"
    }
    output = ""
    for color, values in dice_dict.items():
        if values:
            values = [val for val in values if val is not None]
            if values:
                german_color = color_mapping.get(color, color.upper())
                output += f"{german_color} : {values}, "
    return output.strip(", ")


def reset_last_line(filepath):
    """read csv and remove last line and write again to csv file"""
    if not check_empty_dice_results(filepath):
        with open(filepath, 'r') as file:
            lines = file.readlines()[:-1]
        with open(filepath, 'w') as file:
            file.writelines(lines)

##### Histograms

# helper function to place image on histogarmmplot

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



############## additional binom test



def plot_histogram_bn(ax, df, column_names=['white', 'red']):
    german_dict = {'white':'Weiss - Gewürfelt', 'red':'Rot - Gewürfelt'}
    
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
           alpha=0.1, label=f'Theoretisch', width=bar_width,
           color='blue', hatch='//')

    # Remove numerical x-tick labels and place images instead
    ax.set_xticks([1 + i * bar_width + len(column_names) * bar_width / 2 for i in range(6)])
    ax.set_xticklabels([])  # Remove x-tick labels
    ax.tick_params(axis='both', which='both', length=0)  # Remove axis ticks

    for i in range(1, 7):
        place_image(ax, os.path.join(args.STATPATH, f'side{i}.jpg'), xy=(i, 0), zoom=0.04)

    len_white = len(df['white'].dropna().tolist())
    len_red = len(df['red'].dropna().tolist())

    ax.set_title(f' Anzahl Würfe - Rot: {len_white}, Weiss: {len_red}')
    ax.set_ylabel('Relative Häufigkeit')
    ax.legend()
    
def plot_binomial_test(sample_size, observed, color='white', p_alt=2.5/6, alpha=0.05, ax=None):
    # Define parameters
    p_true = 1/6   # Probability of success for the null hypothesis

    # Calculate critical value for significance level
    critical_value = binom.ppf(1 - alpha, sample_size, p_true)

    # Generate sequence of possible outcomes
    x = np.arange(0, sample_size)

    # Calculate probability mass function values for the null hypothesis
    density_null = binom.pmf(x, sample_size, p_true)

    # Calculate power of the test
    power = 1 - binom.cdf(observed - 1, sample_size, p_alt)

    # Calculate p-value for the observed value under the real distribution
    p_value_observed = 1 - binom.cdf(observed - 1, sample_size, p_true)

    # Plot the density function
    ax.bar(x, density_null, color='blue', hatch='//', edgecolor='black', alpha=0.1, label=f'Theoretisch')

    # Add vertical lines for critical value and observed value
    ax.axvline(x=int(critical_value), color='black', linestyle='--', label=f'95% Quantil: {int(critical_value)}')
    
    if color == 'red':
        ax.axvline(x=int(observed), color='red', linestyle='--', label=f'Anzahl: {int(observed)}')
    else:    
        ax.axvline(x=int(observed), color='grey', linestyle='--', label=f'Anzahl: {int(observed)}')
    
    
    # Add legend
    ax.legend()

    if color == 'red':
        ax.set_title(f'Binomial Test Rot Nr. 3\n')
    if color == 'white':
        ax.set_title(f'Binomial Test Weiss Nr. 6\n')
    
    ax.set_xlabel('Anzahl Erfolge')
    ax.set_ylabel('Relative Häufigkeit')
    
    # Set integer ticks for x-axis
    ax.set_xticks(np.arange(0, sample_size+1, step=1))
    ax.tick_params(axis='x')

    # Customize the frame
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    # Add a text box in front of the plot
    text = f'Power: {power:.2f}\n'
    text += f'P-value: {p_value_observed:.2f}\n\n'
    if p_value_observed < alpha:
        text += "Würfel ist vermutlich gezinkt!"
        text_color = 'red'
    else:
        text += "Kein Beweis für einen gefälschten Würfel!"
        text_color = 'green'
    
    ax.text(0.72, 0.3, text, transform=ax.transAxes,
             bbox=dict(facecolor='white', edgecolor='black', boxstyle='round,pad=1'),
             fontsize=12, color=text_color, ha='center', va='center')


def plot_histogram_and_binomial_tests(data_path):
    
    with matplotlib_lock:
        fig = plt.figure(figsize=(16, 6))  # Adjust the figure size here
        gs = gridspec.GridSpec(2, 2, width_ratios=[1.5, 1], height_ratios=[1, 1])  # Custom grid layout
        
        #count 6es and 3s
        df = pd.read_csv(data_path)
        white_list,red_list = df['white'].dropna().tolist(), df['red'].dropna().tolist()
        
        white_6=  white_list.count(6)
        red_3= red_list.count(3)
        
        ax_histogram = plt.subplot(gs[:, 0])
        plot_histogram_bn(ax_histogram, df)
        
        ax_white_test = plt.subplot(gs[0, 1])
        ax_red_test = plt.subplot(gs[1, 1])
        

        # TODO : change the real probas
        
        if white_6 > 0:
            plot_binomial_test(sample_size=len(white_list), observed=white_6, color='white', p_alt=2.5/6, alpha=0.05, ax=ax_white_test)
        else:
            ax_white_test.axis('off')
        
        if red_3 > 0:
            plot_binomial_test(sample_size=len(red_list), observed=red_3, color='red', p_alt=2.5/6, alpha=0.05, ax=ax_red_test)
        else:
            ax_red_test.axis('off')
                    
        plt.tight_layout()
        #plt.show()

        img = BytesIO()
        plt.savefig(img, format='png')
        img.seek(0)
        plt.close()
        return img