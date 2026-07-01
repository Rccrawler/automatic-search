"""
MoRandom - Generador de números aleatorios con entropía mixta.
Hereda de random.Random pero altera ligeramente los patrones estándar
mezclando entropía del sistema operativo y tiempo en cada operación.
"""

import random
import os
import time
import hashlib


class _MoRandomCore(random.Random):
    """
    Generador interno que extiende random.Random.
    Mezcla el estado interno con entropía externa en cada llamada
    para que el patrón no coincida con la implementación estándar.
    """

    def __init__(self, x=None):
        # Semilla combinada: valor dado + tiempo + bytes del SO
        combined = self._build_seed(x)
        super().__init__(combined)

    def _build_seed(self, x=None):
        """Construye una semilla mezclando múltiples fuentes de entropía."""
        t = time.perf_counter_ns()           # nanosegundos del sistema
        os_bytes = int.from_bytes(os.urandom(8), "big")  # 8 bytes aleatorios del SO
        base = x if x is not None else t
        # Mezclar todo con un hash para que el resultado no sea trivial
        raw = f"{base}|{t}|{os_bytes}".encode()
        digest = int(hashlib.sha256(raw).hexdigest(), 16)
        return digest

    def random(self):
        """
        Genera un float [0.0, 1.0) con una pequeña perturbación.
        Se añade una fracción del tiempo actual para desplazar el valor
        respecto al Mersenne Twister puro.
        """
        base = super().random()
        # Perturbación: fracción de nanosegundos mod 1e-4 (invisible al usuario, pero cambia el estado)
        jitter = (time.perf_counter_ns() % 10_000) / 1e12
        result = (base + jitter) % 1.0
        return result

    def randint(self, a, b):
        """Entero en [a, b] usando la distribución perturbada."""
        return a + int(self.random() * (b - a + 1))

    def randrange(self, start, stop=None, step=1):
        """Rango aleatorio usando random() perturbado."""
        if stop is None:
            stop = start
            start = 0
        width = stop - start
        if step == 1:
            return start + int(self.random() * width)
        # Con step
        n = (width + step - 1) // step
        return start + step * int(self.random() * n)

    def choice(self, seq):
        """Elige un elemento de la secuencia con índice perturbado."""
        if not seq:
            raise IndexError("Cannot choose from an empty sequence")
        idx = int(self.random() * len(seq))
        idx = min(idx, len(seq) - 1)  # salvaguarda
        return seq[idx]

    def shuffle(self, x):
        """
        Fisher-Yates shuffle usando random() perturbado.
        La pausa mínima entre intercambios varía el timing respecto al estándar.
        """
        n = len(x)
        for i in range(n - 1, 0, -1):
            j = int(self.random() * (i + 1))
            j = min(j, i)
            x[i], x[j] = x[j], x[i]

    def sample(self, population, k, *, counts=None):
        """Muestreo sin reemplazo usando random() perturbado."""
        if counts is not None:
            # Expandir población con conteos
            expanded = []
            for elem, c in zip(population, counts):
                expanded.extend([elem] * c)
            population = expanded

        pool = list(population)
        n = len(pool)
        if k > n:
            raise ValueError("Sample larger than population")
        result = []
        for i in range(k):
            j = int(self.random() * (n - i))
            j = min(j, n - i - 1)
            result.append(pool[j])
            pool[j] = pool[n - i - 1]
        return result

    def uniform(self, a, b):
        """Float uniforme entre a y b."""
        return a + self.random() * (b - a)

    def choices(self, population, weights=None, *, cum_weights=None, k=1):
        """Elección con pesos usando random() perturbado."""
        n = len(population)
        if cum_weights is None:
            if weights is None:
                # Sin pesos: uniforme
                return [self.choice(population) for _ in range(k)]
            # Calcular pesos acumulados
            total = 0.0
            cum_weights = []
            for w in weights:
                total += w
                cum_weights.append(total)
        else:
            total = cum_weights[-1]

        result = []
        for _ in range(k):
            r = self.random() * total
            # Búsqueda lineal (población pequeña en este uso)
            for i, cw in enumerate(cum_weights):
                if r <= cw:
                    result.append(population[i])
                    break
            else:
                result.append(population[-1])
        return result


# ── Instancia global (igual que el módulo random estándar) ──────────────────
_inst = _MoRandomCore()

# Funciones de nivel de módulo que usan la instancia global
seed      = _inst.seed
random    = _inst.random
uniform   = _inst.uniform
randint   = _inst.randint
randrange = _inst.randrange
choice    = _inst.choice
choices   = _inst.choices
shuffle   = _inst.shuffle
sample    = _inst.sample

# Re-exportar la clase principal
Random = _MoRandomCore
