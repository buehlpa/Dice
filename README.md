# Distinguish Real from Fake dice

 Dice-Distinguisher-Box, from Zurich University of Applied Sciences (ZHAW).
 **In development!**

A project to display Computer-Vision Machine-Learning and Statistics in a playful way. 


### Current Prototype
<img src="https://github.com/buehlpa/Dice/assets/64488738/46b51cfd-4974-4864-b354-d0685827d79d" width="400">


### Current UI

<img src="https://github.com/buehlpa/Dice/assets/64488738/9fb6b6e5-7055-4a65-aefc-ad5d4ef3be44" width="400">
### Poster

![image](https://github.com/buehlpa/Dice/assets/64488738/65bcf43e-40bd-4e6f-898c-62354c127ece)

### Working Principle

Dices used in this project from: https://trick-dice.com/
- 4 dice are used 2 red and 2 whites, 1 red is biased towards #3 and 1 white is biased towards #6, the others are normal die

- choose 2 dice (1 red and 1 white) from the 4, the other 2 put aside.
- roll the two selected dice at the same time 
- based on the scene detection, the image is automatically taken and sent to processing to identify the die
- Numbers are saved
- statistics of the rolled dice are displayed
- based on a binomial test it is determined whether there is evidence for a manipulated die
- rerun with the same selected dice

### Additional Information on the Steps

#### Computer Vision
With traditional Computer vision, we can distinguish 3 states of the scene "empty scene", "moving scene" and "dice still on the mat scene". If there is a still scene we can send an image to an algorithm that crops out the dice in the images which then get sent to the next step to the CNN

##### State detector
for each of the frames from the video stream, we can calculate a simple metric by subtracting the maximum pixel value from the mean of the grayscale image. If this score is small then we can assume that the image is empty. Based on the difference to the last image's score  we can also infer the "moving scene" state. So the "dice still on the mat scene" is just based on a threshold that has to be set. This simple detection is efficient and proved to be robust.

##### Isolating the individual Dice
If the still state is detected, a single frame is taken and is ready for isolating the dices on the images. By converting the images to the HSV colorspace the removal of the green background is easy, as well as getting the 2 different colors of the dice.

with the ConnectedComponents algorithm as well as the Bounding Rectangle, the isolation is swift. the output of these chained operations are grayscale, nearly quadratic cropped images of the individual dice in the image

#### CNN
There is a small CNN with just 3 layers, an increasing amount of filters, Dropout, and ReLu activation functions with a classification Head at the end and CrossEntropy loss. The network is trained with an augmentation strategy on images like these
![image](https://github.com/buehlpa/Dice/assets/64488738/c6e68c11-3828-4188-b71b-95074504c4f8)
The dataset to train the model is combined from the object detection dataset https://github.com/nell-byler/dice_detection (just cut the dice according to the box coordinates) and own images taken from the dice detector Box.
On a testset with 10 samples each (confusion matrix on the left Accuracy=100%), the outcome distribution (right )indicates that the classes were well-learned by the model.
![image](https://github.com/buehlpa/Dice/assets/64488738/8f528b2b-d547-4cff-8721-49673aa087c5)

Of course, the whole part with traditional CV and the CNN could be replaced by just an object detection pipeline... 


#### Statistical Test
Since the power of a Chisquare test is very low for a small number of rolls it is decided to assume that we are suspicious that the red die might be biased toward 3 and the white die might be biased towards 6
Therefore we can formulate the Null hypothesis that if a die is not fake the true probability is equal to 1/6. Hence we can perform a binomial test to test this for both die with the observed amounts.
To confidently say that this dice is biased towards our suspected numbers we can not solely rely on the p-value of said test. We have to consider the statistical power (The likelihood of not rejecting the Null hypothesis if the alternative is true, or the Probability of making an error of type 2 https://www.statisticshowto.com/probability-and-statistics/statistics-definitions/statistical-power/).
For a more precise power analysis, we'd also need the real probability of the fake die, which we could empirically get by rolling the dice several hundred times. Not that the power of this test is reliant on the true probability of the alternative and also the sample size 

![image](https://github.com/buehlpa/Dice/assets/64488738/ff6f8fbe-b07a-4b51-8ae5-6535a90aa594)


## Installation on UNIX

- clone Repo
```
git clone https://github.com/buehlpa/Dice
```
- go to /app and create
- 
```
python -m venv dice_env
```
- activate environment
```
source dice_env/bin/activate
```
- install dependecies
```
pip install -r requirements_unix.txt
```

- start app

```
python main.py
```

## Hints

This module was tested on a Rasperry PI-5 with Raspian

         
### use the 2560 x 1440 screen resolution , other formats are currently not supported
               
                
               
