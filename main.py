import sys
import getpass
import math
from qiskit import IBMQ
from qiskit import execute
from qiskit import ClassicalRegister, QuantumRegister, QuantumCircuit
from qiskit.providers.ibmq import least_busy
from qiskit import BasicAer

SHOTS = 1024

# configuration for python to write our QASM file

def setShipPosition(player, ship, shipPos):
    positionPicked = False

    while (not positionPicked):
        position = getpass.getpass("Player " + str(player + 1) + ", choose a position for ship " + str(ship + 1) + ". (0, 1, 2, 3, or 4)\n")

        try:
            position = int(position)

            if (position >= 0 and position <= 4 and not (position in shipPos[player])):
                shipPos[player].append(position)
                positionPicked = True
            else:
                print("Not a valid position. Try again.\n")
        except Exception:
            print("Not an integer, please try again.\n")


def bombShip(player, bombPos):
    positionPicked = False

    while (not positionPicked):
        position = input("Player " + str(player + 1) + ", choose a postion to bomb. (0, 1, 2, 3, or 4)\n")

        try:
            position = int(position)

            if (position >= 0 and position <= 4):
                bombPos[player][position] = bombPos[player][position] + 1
                positionPicked = True
            else:
                print("Not a valid position. Try again.\n")
        except Exception:
            print("Not an integer, please try again.\n")


def calculateDamageToShips(grid):
    damage = [[0.0] * 5 for i in range(2)]

    for player in range(2):
        # check all bits
        for key in grid[player].keys():
            for bit in range(5):
                if (key[bit] == "1"):
                    damage[player][4 - bit] = damage[player][4 - bit] + grid[player][key]/SHOTS

    return damage


def displayBoards(damage):
    for player in range(2):
        print("Player " + str(player) + "'s board:\n")
        print("Position     Damage\n")
        for position in range(5):
            print(str(position) + "            " + (str(math.floor(damage[player][position]*100)) + "%\n" if damage[player][position] else "?\n"))
        print("-----------------------\n")


def playGame(device, shipPos):
    gameOver = False
    bombPos = [
        [0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0]
    ]
    grid = [0, 0]

    gameOver = False

    while (not gameOver):
        bombShip(0, bombPos)
        bombShip(1, bombPos)

        for player in range(2):
            print("Measuring damage to Player " + str(player + 1) + "...")

            # Q_SPECS = {
            #     "circuits": [{
            #         "name": "gridScript",
            #         "quantum_registers": [{
            #             "name": "q",
            #             "size": 5
            #         }],
            #         "classical_registers": [{
            #             "name": "c",
            #             "size": 5
            #     }]}],
            # }

            # Q_program = QuantumProgram(specs=Q_SPECS)
            # gridScript = Q_program.get_circuit("gridScript")
            # q = Q_program.get_quantum_registers("q")
            # c = Q_program.get_classical_registers("c")

            q = QuantumRegister(5)
            c = ClassicalRegister(5)

            circ = QuantumCircuit(q, c)

            for position in range(5):
                for hit in range(bombPos[(player + 1) % 2][position]):
                    for ship in range(3):
                        if (position == shipPos[player][ship]):
                            frac = 1/(ship + 1)
                            circ.u3(frac * math.pi, 0.0, 0.0, q[position])

            for qubit in range(5):
                circ.measure(q[qubit], c[qubit])

            # Q_program.set_api(Qconfig.APItoken, Qconfig.config["url"])
            job = execute(circ, device, shots=SHOTS)

            grid[player] = job.result().get_counts(circ)

        if (('Error' in grid[0].values()) or ('Error' in grid[1].values())):
            print("\nThe process timed out. Try this round again.\n")
        else:
            damage = calculateDamageToShips(grid)
            displayBoards(damage)

            for player in range(2):
                if (
                    damage[player][shipPos[player][0]] > 0.95 and
                    damage[player][shipPos[player][1]] > 0.95 and
                    damage[player][shipPos[player][2]] > .95
                ):
                    print("All ships on Player " + str(player) + "'s board are destroyed! \n")
                    gameOver = True

            if (gameOver):
                print("Game Over")


def main():
    d = input("Do you want to play on a real device? (y/n)\n")

    if (d == "y"):
        try:
            IBMQ.load_accounts()
        except:
            token = input("Could not find IBM Q API token. Please generate one at https://quantumexperience.ng.bluemix.net/qx/account/advanced and paste it here: ")
            try:
                IBMQ.save_account(token)
                IBMQ.load_accounts()
            except:
                print("Could not load API Token, please check your token again and rerun this program.")
                exit()

        device = least_busy(IBMQ.backends(simulator=False))

        # device = 'ibmqx2'
    else:
        device = BasicAer.get_backend('qasm_simulator')

    # Read this as shipPos[player][ship] = position of player's ship
    shipPos = [
        [],
        []
    ]

    for i in range(2):
        for j in range(3):
            setShipPosition(i, j, shipPos)

    playGame(device, shipPos)


if __name__ == "__main__":
    main()
