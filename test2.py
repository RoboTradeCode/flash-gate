l = ["a", "b", "c", "d", "e", "f"]

match l:
    case _ if "a" in l:
        print(1)
    case "b", _:
        print(2)
    case ["c"]:
        print(3)
    case ["d", *_]:
        print(4)
    case ["e", "f"]:
        print(5)
    case _:
        print(6)
