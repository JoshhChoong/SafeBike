// import { useState } from 'react'
import './App.css'
import Nav from './components/Nav'
import Search from './components/Search'
import Map from './components/Map'

function App() {
  // const [count, setCount] = useState(0)

  return (
    <div className='wrapper'>

      {/* Remember this has a grid, we might want to remove that later */}
      <div className='wrapper-content'> 

        <Nav></Nav>

        <Search></Search>

         {/* Lower z-index, below nav etc  */}
        <Map></Map>
       
       

      </div>
    </div>
  )
}

export default App
