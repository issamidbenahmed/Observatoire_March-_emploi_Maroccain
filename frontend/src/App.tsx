import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import Jobs from './pages/Jobs';
import Trends from './pages/Trends';
import HistoricalAnalysis from './pages/HistoricalAnalysis';

function App() {
  return (
    <Router>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/jobs" element={<Jobs />} />
          <Route path="/trends" element={<Trends />} />
          <Route path="/history" element={<HistoricalAnalysis />} />
        </Routes>
      </Layout>
    </Router>
  );
}

export default App;
