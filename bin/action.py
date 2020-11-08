from dataclasses import dataclass
import random


@dataclass
class Action:
    communication_time = random.uniform(100, 500)  # ms
    data_amount = random.randint(1000, 3000)  # Bytes

    network_throughput = 125 * (10 ** 3)  # 1 KByte/ms
    network_transfer_time = data_amount / network_throughput

    memory_throughput = 10 ** 6  # 1 MByte/ms
    persist_time = data_amount / memory_throughput

    def get_time(self, is_save_to_disc: bool, is_async: bool) -> float:
        disc_save_time = self.get_disc_save_time(is_save_to_disc, is_async)
        return self.communication_time + self.network_transfer_time + disc_save_time

    def get_disc_save_time(self, is_save_to_disc, is_async: bool):
        return self.persist_time if is_save_to_disc else 0
