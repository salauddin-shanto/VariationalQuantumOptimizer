from qiskit import QuantumCircuit, transpile, Aer, IBMQ, execute
from qiskit.visualization import plot_histogram
import matplotlib.pyplot as plt
from qiskit.transpiler import CouplingMap, PassManager
from qiskit.transpiler.passes import *
from qiskit.circuit.library import QFT, GroverOperator

def create_qft_circuit(n):
    qft_circuit = QFT(n).decompose()  # Convert QFT into basic gates
    return qft_circuit

qc = create_qft_circuit(5)
qc.draw('mpl')

def classical_optimization(qc):
    pass_manager = PassManager([
        RemoveResetInZeroState(),  # Removes redundant resets
        CXCancellation(),  # Merges adjacent CNOTs
        Optimize1qGates(),  # Merges single-qubit gates
        CommutativeCancellation()  # Removes unnecessary swaps
    ])
    return pass_manager.run(qc)

qc_optimized_classical = classical_optimization(qc)
qc_optimized_classical.draw('mpl')

def hardware_aware_optimization(qc, backend_name='ibmq_belem'):
    provider = IBMQ.load_account()
    backend = provider.get_backend(backend_name)
    coupling_map = backend.configuration().coupling_map

    pass_manager = PassManager([
        FullAncillaAllocation(coupling_map),
        EnlargeWithAncilla(),
        ApplyLayout(),
        NoiseAdaptiveLayout(backend),  # Layout optimization for noise reduction
        SabreSwap(coupling_map),  # Swap gate reduction
    ])
    
    return pass_manager.run(qc)

qc_optimized_hardware = hardware_aware_optimization(qc)
qc_optimized_hardware.draw('mpl')

from qiskit.algorithms.optimizers import COBYLA
from qiskit.circuit import Parameter
import numpy as np

def variational_optimization(qc):
    params = [Parameter(f'θ{i}') for i in range(qc.num_qubits)]
    
    for i, param in enumerate(params):
        qc.rx(param, i)  # Add tunable Rx gates

    optimizer = COBYLA()
    initial_params = np.random.rand(len(params))
    optimized_params = optimizer.optimize(len(params), lambda x: np.linalg.norm(x), initial_params)
    
    return qc.bind_parameters(optimized_params[0])

qc_optimized_variational = variational_optimization(qc)
qc_optimized_variational.draw('mpl')

def compare_optimizations(qc_original, qc_optimized):
    print("Original Circuit - Gate Count:", qc_original.count_ops())
    print("Optimized Circuit - Gate Count:", qc_optimized.count_ops())
    print("Original Circuit - Depth:", qc_original.depth())
    print("Optimized Circuit - Depth:", qc_optimized.depth())

compare_optimizations(qc, qc_optimized_hardware)

provider = IBMQ.load_account()
backend = provider.get_backend('ibmq_belem')

job = execute(qc_optimized_hardware, backend=backend, shots=1024)
result = job.result()
counts = result.get_counts()
plot_histogram(counts)
plt.show()

