# **Dog or Frog Solution: A Unique (and Lazy) Approach to ML** (Or “The Bash Approach to Adversarial ML”)

**Background**

I suspect I addressed this problem from a very much unintended angle. Because our team had very little experience with Machine Learning, we decided not to focus too much on this problem because we all agreed learning ML was not really feasible within the time constraints of the competition. That being said, I still was curious. I did some research on the problem, and learned about ‘Adversarial Perturbations.’ Unfortunately for me, all of the guides I found online were not specific to MobileNet and I certainly didn’t have the expertise or time to figure out how to adapt one of the tutorials to work for this problem. However, I soon developed a very rough idea of how to solve the problem.


Mainly for the sake of fun and learning than solving the problem, I decided to write a sort of genetic algorithm to attempt to generate the required adversarial perturbation for the problem.

## First Steps
For any approach really to work, I was going to have to download the model and set it up to run on my computer. The algorithm needs exact feedback on the "froginess" of its output and 
the online model won't provide that unless the 'tree_frog' confidence is in the top 5 predictions (also I didn't want to automate POST requests in python). I downloaded the source and 
began tinkering. After installing all the requirements using pip I began to look at the solution_template.py provided in the static directory. Unfortunately it didn't contain any code to actually run the model, so I looked at some of the code used for the server. I found the necessary methods and shamelessly copy-pasted them into the solution template. After a little tinkering I got the script to output the exact 'tree_frog' confidence of the model.

## The Evolution of Laziness
Before beginning a full on genetic algorithm, I decided to just make sure I could write a script to add some random noise to the dog photo and check the frog similarity and P-Hash value. 


```python
genetic_params = np.array([1, 1])
genetic_data = np.zeros(IMAGE_DIMS)

def genetic_func(j, k, v):
    return v + genetic_data[j][k]

def create_img(...):
    ...
    ...
    for i, line in enumerate(test):
        for j, line2 in enumerate(line):
            for k, pixel in enumerate(line2):
                newImg[i][j][k] = (genetic_func(j, k, pixel[0]), genetic_func(j, k, pixel[1]), genetic_func(j, k, pixel[2]))
```

This worked surprisingly well, so I decided to just use it as the basic image generation code.
Out of pure laziness, I decided that instead of writing a full on genetic algorithm, I would first try just writing a sort of "guess and check" script. This was a lot easier than implementing a genetic algorithm, and as I was running the model on my CPU and not GPU, not much slower.

```python
genetic_last_score = -999999999
number_of_failed_generations = 0
automated_save_ctr = 0

randomness_data = 0.01

if __name__ == "__main__":
    
    import_model()
    
    frog_dist = 9999999
    top_preds = np.array([0, 0])
    
    while frog_dist > 2 or genetic_last_score < 80:
        frog_img = create_img(
            "./autosave{}.png".format(automated_save_ctr),
            "./trixi_frog.png",
            "./model.h5",
            TREE_FROG_STR,
            TREE_FROG_IDX
        )
        frog_mat = prepare_image(frog_img)
        
        # read the image in PIL format
        frog_label, frog_conf, top_preds = get_predictions(frog_mat)
        
        frog_dist = hash_hamming_distance(phash(frog_img), phash(base_img))
        frog_chance = find_frog(top_preds)
        
        if frog_dist > 2:
            score = -9999999999999
        else:
            score = frog_chance
        
        if score >= 95:
            print("noice")
            sys.exit()
        
        
        if genetic_last_score > score:
            # If no improvement then rollback
            print("No Improvement...{}".format(score))
            #print("phash...{}".format(str(frog_dist)))
            genetic_data = np.copy(old_data)
            #print("Rolled Back, Bad Generation!\n")
            number_of_failed_generations = number_of_failed_generations + 1
            
        else:
            # If there was improvement then continue with current params
            print("\nGood Generation, Beginning Backup!")
            genetic_last_score = score
            
            old_data = np.copy(genetic_data)
            print("Finished.")
            frog_img.save("./output.png")
            number_of_failed_generations = 0
            print("isFrog = {}".format(TREE_FROG_STR in frog_label))
            print("pHash = {}".format(frog_dist))
            
            print("frog_confidence = {}".format(frog_chance))
            print("score = {}\n".format(score))
```

Note: The "autosave" feature is due to some a very big performance problem I will explain later.

The next step was creating a function to "evolve" the random data slightly. This ended up being just a basic random function, adding or subtracting a little bit from each value on the genetic_data array.

```python
            # Evolve Alg
            index = 0
            for line in genetic_data:
                jndex = 0
                for pixel in line:
                    change = (random.random()-0.5)*randomness_data
                    genetic_data[index][jndex] = genetic_data[index][jndex] + change
                    
                    jndex += 1
                index += 1
```

This was now a working (barely) basic guess and check algorithm. However it had a really big problem. After leaving the program running for a few minutes, I noticed a very significant slow down. Checking my system resources with htop showed me that my python program had exceeded 20% of my 16GB of RAM and it seemed to not show any sign of slowing. I didn't know that I could have a memory leak in a language with garbage collection.
## The Worst Way to Solve a Memory Leak

I suspected that the leak was related to numpy.copy() somehow not dereferencing old arrays so the python garbage collector wasn't actually deallocating. I suppose I could have carefully rewritten my program carefully and figured out this issue, but I had a far better (worse) idea. Knowing that my guess and check program didn't really need to keep the genetic_data in memory because it was basically stored in ./output.png, I realized I could just restart the program. This is where that autosave feature comes in. It actually didn't really work, but I left it there mostly because I didn't have the inspiration to remove it. In order to implement a proper restart, I wrote the following code in a shell script.

    rm ./autosave*.png
	cp ./output.png ./autosave0.png
	python3 solution_template.py

Now when I run this, it takes the output of the latest guess and uses it as the base image. After confirming that it worked, I added the following to the end of the main loop in solution_template.

     if number_of_failed_generations > 50:
            print("Restarting...")
            os.system("gnome-terminal -x ./restartModel.sh")
            sys.exit(0)
        else:    
            # Evolve Alg    
            ...
Listen it worked, okay?

Gnome-Terminal is great, it just opened in a new tab and then closed the old tab. Contrary to my expectations, it did not flood my screen with terminal windows.

## Progress!
After first being run, the tree_frog confidence was around 1e-11. It improved relatively slowly. After a few minutes it reached 1e-10. From this, I estimated the finishing time to be sometime in the next year or so. However, fortunately after a few hundred more guesses, it became obvious the rate of improvement was exponential. It quickly reached 1e-7 and then 1e-5 etc. After a few hours, it finally reached the 1% frog-like mark. After a total of around 8 hours, the script finally reached 95%. Uploading output.png to the picoCTF website returns the flag.
