// -----------contact form--------
const scriptURL = 'https://script.google.com/macros/s/AKfycbzjcjds6JdAoTg_v8YlARNpIuL2hKGLb_ctHpZRSILvPsTwM5HEgwb1svZOid97qxtZiA/exec'
  const form = document.forms['submit-to-google-sheet']
  const msg = document.getElementById("msg")

  form.addEventListener('submit', e => {
    e.preventDefault()
    fetch(scriptURL, { method: 'POST', body: new FormData(form)})
      .then(response => {
        msg.innerHTML = "Message sent successfully"
        setTimeout(function(){
            msg.innerHTML = ""
        }, 5000)
        form.reset()
    })
      .catch(error => console.error('Error!', error.message))
  })
