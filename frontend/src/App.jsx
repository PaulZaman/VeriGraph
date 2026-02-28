import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import Landing from './pages/Landing'
import HowItWorks from './pages/HowItWorks'
import About from './pages/About'
import Data from './pages/Data'

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/how-it-works" element={<HowItWorks />} />
        <Route path="/about" element={<About />} />
        <Route path="/data" element={<Data />} />
      </Routes>
    </Router>
  )
}

export default App