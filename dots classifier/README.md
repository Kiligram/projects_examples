Task definition - http://www2.fiit.stuba.sk/~kapustik/Klasifikacia.html

Generally, the solution classifies incoming dots into one of the 4 colors according to the nearest neighbours. App generates 20000 dots and then classifies them. When all dots were classified, the graphical representation of the result appeares. There was used k-NN algorithm, where k is initialy set to 1, 3, 7, 15, but can be changed to any other value. 

The solution is optimized, the simple brute force approach would take 330-350 seconds to classify 20000 dots, while this app takes only 31 seconds. Such optimization was possible by dividing the map into grid, so that app calculates the distance only to the dots that are in the near squares, not to all dots on the map.
