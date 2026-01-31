class Dataset:
    """Wrapper pandas pour données épidémiologiques."""
    
    def __init__(self, data, low_memory=True):
        self.df = self._optimize_dataframe(data) if low_memory else data
        self.metadata = {'transformations': []}
    
    def clean(self, drop_na='any'):
        cleaned = self.copy()
        cleaned.df = cleaned.df.dropna(how=drop_na)
        cleaned.metadata['transformations'].append('clean')
        return cleaned
    
    def aggregate_by_date(self, freq='W', date_col='date'):
        aggregated = self.copy()
        aggregated.df = (aggregated.df
                        .set_index(date_col)
                        .resample(freq)
                        .sum()
                        .reset_index())
        return aggregated
    
    @property
    def viz(self):
        from ..viz import DatasetVisualizer
        return DatasetVisualizer(self)