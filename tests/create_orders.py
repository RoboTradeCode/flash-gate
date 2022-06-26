from aeron import Publisher


def main():
    publisher = Publisher("aeron:ipc", 1004)

    try:
        publisher.offer("ping!")
    finally:
        publisher.close()


if __name__ == "__main__":
    main()
