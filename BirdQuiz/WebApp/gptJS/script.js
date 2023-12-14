const quizData = [
    {
      question: "What is this animal?",
      imageSrc: "https://cdn.download.ams.birds.cornell.edu/api/v1/asset/612014131", // Replace with image URL
      options: ["Dog", "Cat", "Bird", "Fish"],
      answer: "Dog"
    },
    // Add more quiz data objects as needed
  ];
  
  const questionElement = document.getElementById('question');
  const imageElement = document.getElementById('image');
  const optionsElement = document.getElementById('options');
  const resultElement = document.getElementById('result');
  const submitButton = document.getElementById('submit');
  
  let currentQuestion = 0;
  let score = 0;
  
  function generateQuiz(numQuestions) {
    const randomQuestions = shuffleArray(quizData).slice(0, numQuestions);
    quizData.length = 0;
    quizData.push(...randomQuestions);
    loadQuestion();
  }
  
  function shuffleArray(array) {
    for (let i = array.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [array[i], array[j]] = [array[j], array[i]];
    }
    return array;
  }
  
  function loadQuestion() {
    const currentQuizData = quizData[currentQuestion];
  
    questionElement.textContent = currentQuizData.question;
    imageElement.src = currentQuizData.imageSrc;
  
    optionsElement.innerHTML = "";
    currentQuizData.options.forEach(option => {
      const button = document.createElement('button');
      button.textContent = option;
      button.classList.add('option-btn');
      optionsElement.appendChild(button);
  
      button.addEventListener('click', () => {
        checkAnswer(option);
      });
    });
  }
  
  function checkAnswer(answer) {
    const currentQuizData = quizData[currentQuestion];
  
    if (answer === currentQuizData.answer) {
      score++;
    }
  
    currentQuestion++;
  
    if (currentQuestion < quizData.length) {
      loadQuestion();
    } else {
      showResult();
    }
  }
  
  function showResult() {
    questionElement.textContent = '';
    imageElement.style.display = 'none';
    optionsElement.style.display = 'none';
    submitButton.style.display = 'none';
  
    resultElement.textContent = `You scored ${score} out of ${quizData.length}!`;
  }
  
  // Example: Generate quiz with 3 questions
  generateQuiz(3);
  