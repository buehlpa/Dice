


### append to results file
def append_to_csv(path, dice_sum):
    csv_file = os.path.join(path, 'res.csv')
    df = pd.DataFrame({'Numbers': [dice_sum]})
    # If the file does not exist, create it with header, else append without header
    if not os.path.isfile(csv_file):
        df.to_csv(csv_file, mode='w', header=True, index=False)
    else:
        df.to_csv(csv_file, mode='a', header=False, index=False)
        
        
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
    with matplotlib_lock:
        df = pd.read_csv(data_path)
        #df[column_name].hist()
        # plt.title(f'Histogram of {column_name}')
        # plt.xlabel(column_name)
        # plt.ylabel('Frequency')  
        rolls=list(df[column_name])      
        # Theoretical distribution for a fair dice (uniform distribution)
        fair_probs = [1/6] * 6  # Since each outcome (1-6) has an equal probability
        
        if len(rolls) != 0:
            # Counting the frequency of each outcome for the unfair dice
            unfair_probs = [rolls.count(i) / len(rolls) for i in range(1, 7)]
            observed_frequencies = [rolls.count(i) for i in range(1, 7)]
            expected_frequencies = [len(rolls) / 6] * 6
            chi_squared_stat, p_value = chisquare(observed_frequencies, f_exp=expected_frequencies)
            # Create the plot
        fig, ax = plt.subplots()
        # Plotting the bar charts
        ax.bar(range(1, 7), fair_probs, alpha=0.3, color='blue', label='Theoretisch', width=0.4)
        if len(rolls) != 0:
            ax.bar([x + 0.4 for x in range(1, 7)], unfair_probs, alpha=0.5, color='red', label='Gewürfelt', width=0.4)
        # Remove numerical x-tick labels and place images instead
        ax.set_xticks(range(1, 7))
        ax.set_xticklabels([])  # Remove x-tick labels
        ax.tick_params(axis='both', which='both', length=0)  # Remove axis ticks
        for i in range(1, 7):
            place_image(ax, os.path.join(STATPATH, f'side{i}.jpg'), xy=(i, 0), zoom=0.04)
        # Adding title and legend
        if len(rolls) != 0:
            plt.title(f'Häufigkeiten von Würfelergebnissen, Anzahl Würfe: {len(rolls)} p= {p_value:.3f}')
        else:
            plt.title(f'Häufigkeiten von Würfelergebnissen, Anzahl Würfe: {len(rolls)}')
        plt.legend()
        # Adjusting the x-axis label position
        plt.xlabel('Würfel Augen', labelpad=30)
        plt.ylabel('Relative Häufigkeit')
                

        img = BytesIO()
        plt.savefig(img, format='png')
        img.seek(0)
        plt.close()
        return img


def reset_histogram():
    csv_file = os.path.join(RESPATH, 'res.csv')
    # Reset the file by writing only the header
    with open(csv_file, 'w') as file:
        file.write('Numbers\n')
    return '', 204  # Return no content status


def close_app():
    global cap
    try:
        if cap.isOpened():
            cap.release()
        tu.stop_workers()
        
        os.kill(os.getpid(), signal.SIGTERM)
        return "Closed Successfully", 200  # Return a success message with a 200 OK status
    except Exception as e:
        return str(e), 500  # Return the error message with a 500 Internal Server Error status if something goes wrong
