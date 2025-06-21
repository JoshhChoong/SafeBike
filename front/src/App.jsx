// import { useState } from 'react'
import './App.css'
import Nav from './components/Nav'

function App() {
  // const [count, setCount] = useState(0)

  return (
    <div className='wrapper'>

      {/* Remember this has a grid, we might want to remove that later */}
      <div className='wrapper-content'> 

        <Nav></Nav>


      </div>
    </div>
  )
}

export default App
