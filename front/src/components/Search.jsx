import './Search.css'

function Search() {

    return (
        <span>
            <h2>Search</h2>
            <div className='search-bar'>
                <input type="text" id='search'></input>
                <i className="bi bi-search"></i>
            </div>

            <div style={{ display: 'flex', gap: '1rem' }}>
                <button>Start Route</button>
                <button className='exit-button'><i className="bi bi-x"></i></button>
            </div>
            
            
        
        
        </span>
    )

}

export default Search;