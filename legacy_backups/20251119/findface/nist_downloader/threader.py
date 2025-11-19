import threading
import multiprocessing
import traceback

class Threader:
    elements_list = None
    next_id = -1

    def __init__(self, elements_list, func_worker, func_save=None, workers=multiprocessing.cpu_count()):

        self.return_list = [None for x in elements_list]
        self.process_end = False

        self.elements_list = elements_list
        self.func_worker = func_worker
        self.func_save = func_save

        self.lock_next_id = threading.Lock()
        self.lock_save = threading.Lock()
        
        # Executa em paralelo
        threads = []
        for i in range(0, workers):
            t = threading.Thread(target=self.run, name=f'worker_{i}')
            t.start()
            threads.append(t)

        # Wait for all threads to finish
        for thread in threads:
            thread.join()

    def get_next_id(self):
        with self.lock_next_id:
            self.next_id += 1

            if self.next_id < len(self.elements_list):
                return self.next_id
            else:
                return None

    # Função de execução do códico em thread
    def run(self):
        try:
            while True:
                next_id = self.get_next_id()
                if next_id is None:  # Se atingiu o ultimo elemento, sai do laco
                    self.process_end = True
                    break
                else:
                    response = self.func_worker(self.elements_list[next_id])
                    # Atribui o retorno da funcao ao array de respostas
                    self.return_list[next_id] = response

                    if response is not None and self.func_save is not None:
                        with self.lock_save:
                            self.func_save(response)
        except Exception as e:
            # print(f'Erro na execucao da thread. {str(e)}')
            print(traceback.format_exc())