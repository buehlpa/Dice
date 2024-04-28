# Automatically Detect Dices 

 Dice detector BOX, from Zurich University of Applied Sciences (ZHAW).
 **In development!**

A project to display Computer Vision Machine Learning and Statistics in a playful way 

### Current Prototype
![image](https://github.com/buehlpa/Dice/assets/64488738/46b51cfd-4974-4864-b354-d0685827d79d)


### Current UI
![image](https://github.com/buehlpa/Dice/assets/64488738/9fb6b6e5-7055-4a65-aefc-ad5d4ef3be44)

### Poster

![image](https://github.com/buehlpa/Dice/assets/64488738/65bcf43e-40bd-4e6f-898c-62354c127ece)

## Installation on UNIX

- clone Repo
- create conda env 

```
conda create -n dice python=3.9.18
```
or
```
python -m venv MYENV
```

```
pip install -r requirements_unix.txt
```

## Hints
Dice/raspberry_run  - this directory contains the code to run on the rasperry PI with limited resources, the core is developed in /workspace 

```
Dice/app/~ python main.py 
```
    
is the functioning version , please develop in the *_dev.py files




Dice/workspace  - train DL models  on machine with gpu 
                - state detector
                - dice side detector 

            - develop Algos to detect dices 
                - greenscreen , eroding, masking etc. 
                
### use the 2560 x 1440 screen resolution , other formats are currently not supported
               
                
                
# Fixing tflite:

tflite runtime with

pip install tensorflow

..
