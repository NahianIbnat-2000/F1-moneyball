"""Few-cluster inference: restricted wild cluster bootstrap tests of H0: beta = beta0, and confidence
intervals by test inversion.

The interval is the set of beta0 values that the same bootstrap test does not reject at 5%, so the
interval and the bootstrap p-value come from one procedure (MacKinnon and Webb 2017; Roodman et al. 2019).
The same Webb weight draws are used for every beta0, so the p-value is a smooth step function of beta0
and the bisection is well defined. Results are associations, not causal effects.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import patsy

WEBB = np.array([-np.sqrt(1.5), -1.0, -np.sqrt(0.5), np.sqrt(0.5), 1.0, np.sqrt(1.5)])


class WildCluster:
    """Restricted wild cluster bootstrap for one coefficient, vectorised over draws."""

    def __init__(self, formula: str, data: pd.DataFrame, var: str, cluster: str, draws: int = 9999,
                 seed: int = 20261119):
        y, X = patsy.dmatrices(formula, data, return_type="dataframe")
        self.j = list(X.columns).index(var)
        self.y, self.X = y.to_numpy().ravel(), X.to_numpy()
        groups = data.loc[X.index, cluster].to_numpy()
        self.G = np.unique(groups)
        self.idx = np.searchsorted(self.G, groups)
        n, k = self.X.shape
        self.A = np.linalg.pinv(self.X.T @ self.X)
        self.c = len(self.G) / (len(self.G) - 1) * (n - 1) / (n - k)
        self.Xr = np.delete(self.X, self.j, axis=1)
        self.Pr = self.Xr @ np.linalg.pinv(self.Xr)            # projection onto the restricted model
        rng = np.random.default_rng(seed)
        self.W = rng.choice(WEBB, size=(draws, len(self.G)))   # same draws for every beta0
        b, t = self._t(self.y[:, None], 0.0)
        self.beta, self.se = float(b[0]), float(b[0] / t[0])

    def _t(self, Y: np.ndarray, beta0: float) -> tuple[np.ndarray, np.ndarray]:
        """Coefficient j and its CR1 t statistic against beta0, for each column of Y."""
        B = self.A @ self.X.T @ Y
        U = Y - self.X @ B
        S = np.zeros((len(self.G), self.X.shape[1], Y.shape[1]))
        np.add.at(S, self.idx, self.X[:, :, None] * U[:, None, :])
        a = self.A[self.j]                                      # row j of (X'X)^-1
        v = self.c * np.einsum("k,gkb->gb", a, S) ** 2
        se = np.sqrt(v.sum(axis=0))
        return B[self.j], (B[self.j] - beta0) / se

    def p_value(self, beta0: float = 0.0) -> float:
        """Two-sided bootstrap p-value for H0: beta = beta0, with the null imposed."""
        y0 = self.y - beta0 * self.X[:, self.j]
        fit = self.Pr @ y0
        resid = y0 - fit
        Ystar = (fit[:, None] + resid[:, None] * self.W[:, self.idx].T) + beta0 * self.X[:, self.j][:, None]
        _, tstar = self._t(Ystar, beta0)
        t_obs = (self.beta - beta0) / self.se
        return float((np.abs(tstar) >= abs(t_obs)).mean())

    def ci(self, level: float = 0.95, tol: float = 1e-4) -> tuple[float, float]:
        """Confidence interval by inverting the bootstrap test; nan where the interval is unbounded."""
        alpha = 1 - level

        def edge(direction: int) -> float:
            inside = self.beta
            step = 2 * abs(self.se) or 1.0
            outside = inside + direction * step
            for _ in range(40):                                 # widen until the test rejects
                if self.p_value(outside) < alpha:
                    break
                inside, outside = outside, outside + direction * step
                step *= 2
            else:
                return float("nan")
            while abs(outside - inside) > tol * max(1.0, abs(self.se)):
                mid = (inside + outside) / 2
                if self.p_value(mid) < alpha:
                    outside = mid
                else:
                    inside = mid
            return (inside + outside) / 2

        return edge(-1), edge(1)
