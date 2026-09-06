(function () {
  const durationSeconds = 3 * 60;
  let intervalId;
  let deadline;

  function formatTime(seconds) {
    const minutes = Math.floor(seconds / 60);
    const remainder = seconds % 60;
    return `${minutes}:${String(remainder).padStart(2, '0')}`;
  }

  function start(onExpired) {
    const timerElement = document.querySelector('#quizTimer');
    if (!timerElement) return;
    clearInterval(intervalId);
    deadline = Date.now() + durationSeconds * 1000;
    timerElement.hidden = false;
    timerElement.classList.remove('expired');

    function tick() {
      const secondsLeft = Math.max(0, Math.ceil((deadline - Date.now()) / 1000));
      timerElement.textContent = `TIME LEFT ${formatTime(secondsLeft)}`;
      if (secondsLeft === 0) {
        clearInterval(intervalId);
        timerElement.classList.add('expired');
        onExpired();
      }
    }

    tick();
    intervalId = setInterval(tick, 250);
  }

  function stop() {
    clearInterval(intervalId);
  }

  window.quizTimer = {start, stop};
})();