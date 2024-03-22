import requests
import queue
from loguru import logger
import pickle
import signal
import sys


REGEX_5 = "\b{0}{1}{2}{3}{4}\b"
REGEX_6 = "\b{0}{1}{2}{3}{4}{5}\b"
REGEX_ANYCHR = "[a-zA-Z]"
BEGIN_WORD = "spear"
END_WORD = "hello"


class Nod:
    """
    self.word: str
    self.path: paths
    self.dep: deep
    self.dist: distance
    self.begin: BEIGN/END
    """

    def __init__(self, word, parent=None, begin="NONE"):
        self.word = word
        self.begin = begin # BEGIN/END
        if parent:
            self.path = parent.path + [parent.word]
            self.dep = parent.dep + 1
        else:
            self.path = []
            self.dep = 0

    def getsAll(self) -> list:
        res = []
        word = list(self.word)
        for idx in range(5):
            c = word[idx]
            word[idx] = "_"
            res.append("".join(word))
            word[idx] = c
        return res



BEGIN_NOD = Nod(BEGIN_WORD)
END_NOD = Nod(END_WORD)
HAVE_FIND = {}


def getUrl(word: str) -> str:
    return "https://wordledictionary.com/.netlify/functions/query?find={0}&has=&not=&limit=undefined".format(
        word   
    )


def getWord(word: str) -> tuple:
    logger.info("wants to get word: {0}".format(word))
    if HAVE_FIND.get(word, False) != False:
        logger.info("have already gets, return data in memory")
        return HAVE_FIND.get(word)
    else:
        logger.warning("havn't, now get from api")
        try:
            resp = requests.get(getUrl(word))
            respJson = resp.json()
            resp.close()
        except:
            logger.error("ERROR!")
            logger.info("now saving... ")
            save()
            logger.info("finish saving... now quit the program...")
        else:
            logger.info("Finish! correctly")
            HAVE_FIND[word] = respJson["results_length"], respJson["results"]
            logger.info("finished save")
            return HAVE_FIND.get(word)


def wordsFromResults(respJson: tuple) -> list:
    resp = respJson[1]
    res = []
    for ele in resp:
        res.append(ele["word"])
    return res


def pre():
    from time import sleep

    global HAVE_FIND
    logger.info("try to load data...")
    from os import path

    if path.exists("words.pkl"):
        logger.info("exist! loading...")
        with open("words.pkl", "rb") as f:
            HAVE_FIND = pickle.load(f)
        logger.info("finish loading {0} words from saving data".format(len(HAVE_FIND)))
        sleep(1)
        with open("this_time.log", "w") as f:
            f.write(str(HAVE_FIND))
    else:
        logger.warning("didn't find data, it will be created this term")
        HAVE_FIND = {}


def bfs():
    counts = 0
    Q = queue.Queue()
    disc = {}
    paths = {}
    Q.put(BEGIN_NOD)
    Q.put(END_NOD)
    disc[BEGIN_NOD.word] = "BEGIN"
    disc[END_NOD.word] = "END"

    alreadyFind = False

    while not Q.empty():
        counts += 1
        frnt = Q.get()
        logger.info(
            "BFS finding... dep {0}, path {1}, word {3}:{2}".format(
                frnt.dep, frnt.path, frnt.word, counts
            )
        )
        logger.info(
            "BFS Queue Size {0}".format(
                Q.qsize()
            )
        )
        ways = frnt.getsAll()
        canGo = []
        for way in ways:
            canGo += wordsFromResults(getWord(way))
        for word in canGo:
            logger.info("BFS want to add {0}".format(word))
            if disc.get(word, "NOTIN") == "NOTIN":
                disc[word] = disc[frnt.word]
                Q.put(Nod(word, frnt))
                logger.info("Added! to {0}".format(disc[word]))
                paths[word] = Nod(word, frnt).path
            else:
                logger.info("already in!")
            logger.debug(
                "this word: {0}, frnt: {1}".format(
                    disc.get(word, "NOTIN"), disc.get(frnt.word, "NOTIN")
                )
            )
            if "BEGIN" in ([disc.get(word, "NOTIN"), disc.get(frnt.word, "NOTIN")]):
                if "END" not in (
                    [disc.get(word, "NOTIN"), disc.get(frnt.word, "NOTIN")]
                ):
                    continue
                logger.warning("find! ")
                alreadyFind = True
                logger.info(str([paths[word], word, frnt.word, paths[frnt.word][::-1]]))
                break
        if alreadyFind:
            break


def save():
    logger.info("in save(): begin to save data...")
    global HAVE_FIND
    with open("words.pkl", "wb") as f:
        pickle.dump(HAVE_FIND, f)
    logger.info("finish saving {0} words data".format(len(HAVE_FIND)))


def signal_handler(signal, frame):
    logger.error("catch User Break the program, begining saving data...")
    save()
    logger.info("finish save")
    sys.exit(0)


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    logger.add("output_log.log")
    pre()
    bfs()
    save()
