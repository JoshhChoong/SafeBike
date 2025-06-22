import './Map.css'

function Map(){

    return (
        <div className='map-content'>

            {/* TEST: REMOVE!!!!!!!!! */}
            
            <iframe
                src="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d2886.5258249255345!2d-79.38393498450003!3d43.65322677912125!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x882b34d5e4e5c9e3%3A0x43e7eeb3e63b83fe!2sToronto%2C%20ON!5e0!3m2!1sen!2sca!4v1718998990000!5m2!1sen!2sca"
                width="100%"
                height="100%"
                style={{ border: 0 }}
                allowFullScreen=""
                loading="lazy"
                referrerPolicy="no-referrer-when-downgrade"
            ></iframe>
           
          

        </div>

    )


}


export default Map