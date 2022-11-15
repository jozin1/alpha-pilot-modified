
from Multi_Test.Process2 import Process2
from Multi_Test.Proccess1 import Process1
from multiprocessing import Process, Pipe


if __name__ == '__main__':
    if __name__ == '__main__':
        parent_conn, child_conn = Pipe()

        proc1 = Process1(parent_conn)
        proc2 = Process2(child_conn)

        p1 = Process(target=proc1.start)
        p2 = Process(target=proc2.start)

        p1.start()
        p2.start()
        p1.join()
        p2.join()