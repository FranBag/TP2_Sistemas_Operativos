import random
import threading
import time


# Clase de procesos
class Process:
    def __init__(self, id, size_memory, execution_time):
        self.id = id
        self.size_memory = size_memory
        self.execution_time = execution_time
        self.state = "Listo"
        self.resource = None  # Recurso que utilizará el proceso
        self.blocked = False  

    # Pide un recurso alteatorio
    def request_resource(self, resources):
        self.resource = random.choice(resources)
        if self.resource.locked:
            self.blocked = True
            self.state = "Bloqueado"
        else:
            self.resource.locked = True
            self.state = "Ejecutando"

    # libera un recurso
    def release_resource(self):
        if self.resource:
            self.resource.locked = False
            self.resource = None
            self.state = "Listo"


# Clase de recurso
class Resource:
    def __init__(self):
        self.locked = False  # Estado del recurso


# Clase para administrar la memoria
class MemoryManager:
    def __init__(self, total_memory, algorithm):
        self.total_memory = total_memory
        self.algorithm = algorithm  # Algoritmo que utilizará
        self.used_memory = 0
        self.free_memory = total_memory
        self.page_size = 100
        self.resources = [Resource() for _ in range(NUM_RECURSOS)]  # Lista de recursos
        self.process_memory_map = {}  # Mapa para rastrear la memoria ocupada por cada proceso

    # Añade un proceso según el algoritmo seleccionado
    def add_process(self, process):
        if self.algorithm == "Paginacion":
            return self.add_process_pagination(process)
        elif self.algorithm == "Compactación":
            return self.add_process_compaction(process)
        return False

    def add_process_pagination(self, process):
        required_pages = (process.size_memory + self.page_size - 1) // self.page_size
        if self.free_memory >= required_pages * self.page_size:
            self.used_memory += required_pages * self.page_size
            self.free_memory -= required_pages * self.page_size
            self.process_memory_map[process.id] = required_pages  # Guardar cuántas páginas ocupó
            return True
        return False
    
    def add_process_compaction(self, process):
        if self.free_memory >= process.size_memory:
            self.used_memory += process.size_memory
            self.free_memory -= process.size_memory
            return True
        return False

    def release_memory(self, process):
        if self.algorithm == "Paginacion":
            if process.id in self.process_memory_map:
                pages_freed = self.process_memory_map.pop(process.id)
                self.used_memory -= pages_freed * self.page_size
                self.free_memory += pages_freed * self.page_size
                self.used_memory = max(self.used_memory, 0)
                self.free_memory = min(self.free_memory, self.total_memory)
        elif self.algorithm == "Compactación":
            self.used_memory -= process.size_memory
            self.free_memory += process.size_memory
            self.used_memory = max(self.used_memory, 0)
            self.free_memory = min(self.free_memory, self.total_memory)

    def get_memory_status(self):
        if self.algorithm == "Paginacion":
            return {
                "total": self.total_memory,
                "used": self.used_memory,
                "free": self.free_memory,
                "pages": self.used_memory // self.page_size,
            }
        elif self.algorithm == "Compactación":
            return {
                "total": self.total_memory,
                "used": self.used_memory,
                "free": self.free_memory,
            }


# Clase del administrador de procesos
class ProcessManager:
    def __init__(self, total_memory, algorithm):
        self.memory_manager = MemoryManager(total_memory, algorithm)
        self.ready_queue = []
        self.waiting_queue = []

    def add_process(self, process):
        # Intenta agregar el proceso a la memoria
        if self.memory_manager.add_process(process):
            self.ready_queue.append(process)
        else:
            # Si no entra en la memoria se lo manda a la waiting queue
            self.waiting_queue.append(process)

    def run_processes(self):
        self.update_ready_queue()
        for process in self.ready_queue:
            process.request_resource(self.memory_manager.resources)

            if process.blocked:
                # Mover a la waiting queue si está bloqueado
                self.waiting_queue.append(process)
                self.ready_queue.remove(process)
            else:
                time.sleep(process.execution_time)
                process.release_resource()
                self.memory_manager.release_memory(process)
                self.ready_queue.remove(process)
                process.state = "Terminado"
                return process 

        self.update_ready_queue()

    def update_ready_queue(self):
        # Actualiza la ready queue verificando la waiting queue
        for process in self.waiting_queue:
            if not process.blocked and self.memory_manager.add_process(process):
                self.ready_queue.append(process)
                self.waiting_queue.remove(process)



from PyQt5.QtWidgets import (
    QProgressBar,
    QVBoxLayout,
    QComboBox
)
import sys
import random
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QWidget,
    QLabel,
)
from PyQt5.QtCore import QTimer, QThread, pyqtSignal
from PyQt5.QtCore import QThread, pyqtSignal, pyqtSlot


class ProcessWorkerThread(QThread):
    finished = pyqtSignal(Process)  # Señal para emitir cuando un proceso ha terminado
    process_updated = pyqtSignal(Process) # Señal para actualizar el proceso en ejecución

    def __init__(self, process_manager, parent=None):
        super().__init__(parent)
        self.process_manager = process_manager

    def run(self):
        self.process_updated.emit(self.process_manager.ready_queue[0])
        if self.process_manager.ready_queue:
            process = self.process_manager.run_processes()
            if process:
                self.process_updated.emit(process)  # Actualiza el proceso en ejecución
                self.finished.emit(process)
            time.sleep(0.01)




class ProcessSimulatorGUI(QMainWindow):
    def __init__(self, process_manager):
        super().__init__()
        self.process_manager = process_manager
        self.finished_processes = []
        self.current_thread = None
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Simulador de Procesos")

        main_layout = QVBoxLayout()

        # Combobox de selección de algortimo
        self.algorithm_combo = QComboBox()
        self.algorithm_combo.addItems(["Paginacion", "Compactación"])
        self.algorithm_combo.currentTextChanged.connect(self.update_algorithm)
        main_layout.addWidget(QLabel("Seleccionar algoritmo de memoria:"))
        main_layout.addWidget(self.algorithm_combo)

        tables_layout = QHBoxLayout()

        # Tabla de Ready Queue 
        ready_queue_layout = QVBoxLayout()
        ready_label = QLabel("Ready Queue")
        self.ready_table = QTableWidget(0, 4)
        self.ready_table.setHorizontalHeaderLabels(
            ["ID", "Memoria", "Tiempo", "Estado"]
        )
        ready_queue_layout.addWidget(ready_label)
        ready_queue_layout.addWidget(self.ready_table)

        # Tabla de Waiting Queue
        waiting_queue_layout = QVBoxLayout()
        waiting_label = QLabel("Waiting Queue")
        self.waiting_table = QTableWidget(0, 4)
        self.waiting_table.setHorizontalHeaderLabels(
            ["ID", "Memoria", "Tiempo", "Estado"]
        )
        waiting_queue_layout.addWidget(waiting_label)
        waiting_queue_layout.addWidget(self.waiting_table)

        # Tabla de Recursos
        resources_layout = QVBoxLayout()
        resources_label = QLabel("Estado de Recursos")
        self.resources_table = QTableWidget(0, 2)
        self.resources_table.setHorizontalHeaderLabels(["Recurso", "Estado"])
        resources_layout.addWidget(resources_label)
        resources_layout.addWidget(self.resources_table)

        tables_layout.addLayout(ready_queue_layout)
        tables_layout.addLayout(waiting_queue_layout)
        tables_layout.addLayout(resources_layout)
        main_layout.addLayout(tables_layout)

        # Proceso en ejecución
        self.current_memory_label = QLabel(
            f"Memoria actual: {self.process_manager.memory_manager.free_memory}"
        )
        self.current_process_label = QLabel("Proceso en ejecución: Ninguno")
        self.algorithm_label = QLabel(
            f"Algoritmo usado: {self.process_manager.memory_manager.algorithm}"
        )

        main_layout.addWidget(self.current_memory_label)
        main_layout.addWidget(self.current_process_label)
        main_layout.addWidget(self.algorithm_label)

        # Barra de uso memoria
        self.memory_progress_bar = QProgressBar()
        self.memory_progress_bar.setMaximum(self.process_manager.memory_manager.total_memory)
        main_layout.addWidget(self.memory_progress_bar)

        # Tabla de Procesos Terminados
        finished_label = QLabel("Procesos Terminados")
        self.finished_table = QTableWidget(0, 3)
        self.finished_table.setHorizontalHeaderLabels(
            ["ID", "Memoria", "Estado"]
        )
        main_layout.addWidget(finished_label)
        main_layout.addWidget(self.finished_table)

        # Botón para agregar procesos
        self.add_process_button = QPushButton("Agregar Proceso")
        self.add_process_button.clicked.connect(self.add_process)
        main_layout.addWidget(self.add_process_button)

        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        # Actualizar interfaz
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_interface)
        self.timer.start(100)

    # Actualiza la interfaz dependiendo del algoritmo seleccionado
    def update_algorithm(self):
        if not self.process_manager.ready_queue and not self.process_manager.waiting_queue:
            selected_algorithm = self.algorithm_combo.currentText()
            self.process_manager.memory_manager.algorithm = selected_algorithm
            if selected_algorithm == "Paginacion":
                pages = self.process_manager.memory_manager.get_memory_status()["pages"]
                self.algorithm_label.setText(f"Algoritmo usado: {selected_algorithm}, Páginas: {pages}")
            else:
                self.algorithm_label.setText(f"Algoritmo usado: {selected_algorithm}")

    # Crea un nuevo proceso
    def add_process(self):

        id = (
            len(self.process_manager.ready_queue)
            + len(self.process_manager.waiting_queue)
            + len(self.finished_processes)
        )
        # Valores aleatorios para el proceso
        size_memory = random.randint(50, 200)
        execution_time = random.randint(1, 5)

        new_process = Process(id, size_memory, execution_time)
        self.process_manager.add_process(new_process)

        self.update_interface()

    #AAAAAAAAAAA
    def start_process_thread(self):
        if (self.process_manager.ready_queue) and (
            self.current_thread is None or not self.current_thread.isRunning()
        ):
            self.current_thread = ProcessWorkerThread(self.process_manager)
            self.current_thread.process_updated.connect(
                self.update_current_process_from_thread
            )
            self.current_thread.finished.connect(self.add_to_finished_processes)
            self.current_thread.start()

            self.algorithm_combo.setDisabled(True)

    # Actualiza la interfaz
    def update_interface(self):
        self.start_process_thread()
        self.update_table(self.ready_table, self.process_manager.ready_queue)
        self.update_table(self.waiting_table, self.process_manager.waiting_queue)
        self.update_current_memory()
        self.update_finished_table()
        self.update_memory_progress()
        self.update_resources_table()

        if not self.process_manager.ready_queue and not self.process_manager.waiting_queue:
            self.algorithm_combo.setDisabled(False)

        if self.process_manager.memory_manager.algorithm == "Paginacion":
            pages = self.process_manager.memory_manager.get_memory_status()["pages"]
            self.algorithm_label.setText(f"Algoritmo usado: {self.process_manager.memory_manager.algorithm}, Páginas: {pages}")

    def update_table(self, table, queue):
        table.setRowCount(len(queue))
        for row, process in enumerate(queue):
            table.setItem(row, 0, QTableWidgetItem(str(process.id)))
            table.setItem(row, 1, QTableWidgetItem(str(process.size_memory)))
            table.setItem(row, 2, QTableWidgetItem(str(process.execution_time)))
            table.setItem(row, 3, QTableWidgetItem(str(process.state)))
        
    def update_current_memory(self):
        current_memory = self.process_manager.memory_manager.free_memory
        self.current_memory_label.setText(f"Memoria actual: {current_memory}")

    def update_memory_progress(self):
        memory_status = self.process_manager.memory_manager.get_memory_status()
        self.memory_progress_bar.setValue(memory_status["used"])

    @pyqtSlot(Process)
    def update_current_process_from_thread(self, process):
        self.current_process_label.setText(
            f"Proceso en ejecución: ID:{process.id}, Tamaño:{process.size_memory} B, Tiempo:{process.execution_time}"
        )
        self.update_interface()

    def update_finished_table(self):
        # Actualiza la tabla de procesos terminados
        self.finished_table.setRowCount(len(self.finished_processes))
        for row, process in enumerate(self.finished_processes):
            self.finished_table.setItem(row, 0, QTableWidgetItem(str(process.id)))
            self.finished_table.setItem(row, 1, QTableWidgetItem(str(process.size_memory)))
            self.finished_table.setItem(row, 2, QTableWidgetItem(str(process.state)))

    def add_to_finished_processes(self, process):
        self.finished_processes.append(process)
        self.update_finished_table()

    def update_resources_table(self):
        self.resources_table.setRowCount(len(self.process_manager.memory_manager.resources))
        for row, resource in enumerate(self.process_manager.memory_manager.resources):
            state = "Bloqueado" if resource.locked else "Disponible"
            self.resources_table.setItem(row, 0, QTableWidgetItem(f"Recurso {row + 1}"))
            self.resources_table.setItem(row, 1, QTableWidgetItem(state))



MEMORIA = 1000  # Memoria total
ALGORITMO = "Paginacion"  # Puede ser "Paginacion" o "Compactación"
NUM_RECURSOS = 3  # Cantidad de recursos

if __name__ == "__main__":
    app = QApplication(sys.argv)

    manager = ProcessManager(MEMORIA, ALGORITMO)

    gui = ProcessSimulatorGUI(manager)
    gui.show()

    sys.exit(app.exec_())
