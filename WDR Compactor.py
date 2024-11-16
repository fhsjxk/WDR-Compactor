from WDRCompactor import drawable110
import time
import sys

def main(argv:list):
    c = True
    fixZ2 = True

    try:
        argv[1]
        c = False
    except:
        pass

    if c:
        while True:
            print("Input or drag file into window")

            i = input()
            i = i.strip('"')

            if i.endswith(".wdr") or i.endswith(".wft"):
                drawable110.reduce_size([i], fixZ2)

            elif i.endswith(".ydr") or i.endswith(".yft"):
                print("ydr and yft not supports yet", end="\n\n")
                continue

            elif i == "fixZ2":
                fixz2 = True

            else:
                print("File", i, "does not include a drawable (gta4) file!")
                continue

            print("\nFile compressed " + i, end="\n\n")

    if "fixZ2" in argv[1:]:
        fixz2 = True
        
    for i in argv[1:]:
        if type(i) != str:
            print("Invalid input ", i)
            continue

        if i.endswith(".wdr") or i.endswith(".wft"):
            drawable110.reduce_size([i], fixZ2)

        elif i.endswith(".ydr") or i.endswith(".yft"):
            print("ydr and yft not supports yet", end="\n\n")
            continue

        else:
            print("File ", i, "does not include a drawable (gta4) file!")
            continue
            
        print("File compressed " + i, end="\n\n")

if __name__ == "__main__":
    #main([0, "X:\\Users\\qwert\\Desktop\\DeskTop6\\ofTest\\of\\taxi.wft"])
    main(sys.argv)
    time.sleep(1000)