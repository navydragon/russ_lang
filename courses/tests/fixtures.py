NS = 'http://www.ispringsolutions.com/ispring/quizbuilder/quizresults'

QUIZ_HEADER = (
    f'<quizReport xmlns="{NS}" version="2">'
    '<quizSettings quizType="graded" maxScore="10" timeLimit="0"><passingPercent>80</passingPercent></quizSettings>'
    '<summary score="10" percent="100" time="60" finishTimestamp="8 июня 2026 г. 13:27" passed="true"/>'
    '<questions>'
)
QUIZ_FOOTER = '</questions><groups/></quizReport>'


def wrap_question(question_xml: str) -> str:
    return QUIZ_HEADER + question_xml + QUIZ_FOOTER


SAMPLE_MULTIPLE_CHOICE_XML = (
    '<quizReport xmlns="http://www.ispringsolutions.com/ispring/quizbuilder/quizresults" version="2">'
    '<quizSettings quizType="graded" maxScore="10" maxNormalizedScore="100" timeLimit="0">'
    '<passingPercent>80</passingPercent></quizSettings>'
    '<summary score="10" percent="100" time="3" finishTimestamp="8 июня 2026 г. 13:27" passed="true"/>'
    '<questions><multipleChoiceQuestion id="q1" status="correct" evaluationEnabled="true" maxPoints="10" '
    'maxAttempts="1" awardedPoints="10" usedAttempts="1">'
    '<direction><text>Select the correct answer option:</text></direction>'
    '<feedback><text>That\'s right!</text></feedback>'
    '<answers correctAnswerIndex="0" userAnswerIndex="0">'
    '<answer><text>Option 1</text></answer><answer><text>Option 2</text></answer>'
    '</answers></multipleChoiceQuestion></questions>'
    '<groups><group name="Group 1" passingScore="8" awardedScore="10" maxScore="10" '
    'passingPercent="80" awardedPercent="100" totalQuestions="1" answeredQuestions="1"/></groups>'
    '</quizReport>'
)

QUESTION_FIXTURES = {
    'trueFalseQuestion': wrap_question(
        '<trueFalseQuestion id="q-tf" status="incorrect" evaluationEnabled="true" maxPoints="1" awardedPoints="0">'
        '<direction><text>True or false?</text></direction>'
        '<answers correctAnswerIndex="0" userAnswerIndex="1">'
        '<answer><text>True</text></answer><answer><text>False</text></answer>'
        '</answers></trueFalseQuestion>'
    ),
    'multipleResponseQuestion': wrap_question(
        '<multipleResponseQuestion id="q-mr" status="partially" evaluationEnabled="true" maxPoints="2" awardedPoints="1">'
        '<direction><text>Select all that apply</text></direction>'
        '<answers><answer correct="true" selected="true"><text>A</text></answer>'
        '<answer correct="true" selected="false"><text>B</text></answer>'
        '<answer correct="false" selected="true"><text>C</text></answer></answers>'
        '</multipleResponseQuestion>'
    ),
    'typeInQuestion': wrap_question(
        '<typeInQuestion id="q-ti" status="correct" evaluationEnabled="true" userAnswer="Paris">'
        '<direction><text>Capital of France?</text></direction>'
        '<acceptableAnswers><answer>Paris</answer><answer>paris</answer></acceptableAnswers>'
        '</typeInQuestion>'
    ),
    'fillInTheBlankQuestion': wrap_question(
        '<fillInTheBlankQuestion id="q-fib" status="correct" evaluationEnabled="true">'
        '<direction><text>Fill blanks</text></direction>'
        '<details><text>The </text><blank userAnswer="cat" correct="true"><answer>cat</answer></blank>'
        '<text> sat.</text></details></fillInTheBlankQuestion>'
    ),
    'multipleChoiceTextQuestion': wrap_question(
        '<multipleChoiceTextQuestion id="q-mct" status="correct" evaluationEnabled="true">'
        '<direction><text>Choose words</text></direction>'
        '<details><text>I </text><blank userAnswerIndex="0" correctAnswerIndex="0">'
        '<answer>am</answer><answer>is</answer></blank><text> happy.</text></details>'
        '</multipleChoiceTextQuestion>'
    ),
    'matchingQuestion': wrap_question(
        '<matchingQuestion id="q-match" status="correct" evaluationEnabled="true">'
        '<direction><text>Match items</text></direction>'
        '<premises><premise><text>1</text></premise><premise><text>2</text></premise></premises>'
        '<responses><response><text>A</text></response><response><text>B</text></response></responses>'
        '<matches><match premiseIndex="0" responseIndex="0"/><match premiseIndex="1" responseIndex="1"/></matches>'
        '<userAnswer><match premiseIndex="0" responseIndex="0"/><match premiseIndex="1" responseIndex="1"/></userAnswer>'
        '</matchingQuestion>'
    ),
    'sequenceQuestion': wrap_question(
        '<sequenceQuestion id="q-seq" status="correct" evaluationEnabled="true">'
        '<direction><text>Order items</text></direction>'
        '<answers><answer originalIndex="1"><text>Second</text></answer>'
        '<answer originalIndex="0"><text>First</text></answer></answers>'
        '</sequenceQuestion>'
    ),
    'wordBankQuestion': wrap_question(
        '<wordBankQuestion id="q-wb" status="correct" evaluationEnabled="true">'
        '<direction><text>Word bank</text></direction>'
        '<details><text>The </text><blank userAnswer="sky" correct="true">sky</blank></details>'
        '<words><word>tree</word></words></wordBankQuestion>'
    ),
    'essayQuestion': wrap_question(
        '<essayQuestion id="q-essay" status="answered" evaluationEnabled="false">'
        '<direction><text>Write an essay</text></direction>'
        '<userAnswer>My long answer here.</userAnswer></essayQuestion>'
    ),
    'numericQuestion': wrap_question(
        '<numericQuestion id="q-num" status="correct" evaluationEnabled="true" userAnswer="42">'
        '<direction><text>Enter number</text></direction>'
        '<answers><equal>42</equal><between><leftOperand>40</leftOperand>'
        '<rightOperand>45</rightOperand></between></answers></numericQuestion>'
    ),
    'hotspotQuestion': wrap_question(
        '<hotspotQuestion id="q-hs" status="correct" evaluationEnabled="true">'
        '<direction><text>Click hotspot</text></direction>'
        '<userAnswer><point x="10" y="20"/></userAnswer>'
        '<hotspots><rectangle x="0" y="0" width="100" height="100" marked="true" label="Zone" correct="true"/></hotspots>'
        '</hotspotQuestion>'
    ),
    'likertScaleQuestion': wrap_question(
        '<likertScaleQuestion id="q-likert" status="answered" evaluationEnabled="false">'
        '<direction><text>Rate statements</text></direction>'
        '<statements><statement><text>Statement 1</text></statement></statements>'
        '<scaleLabels numberFromZero="true"><label>Low</label><label>High</label></scaleLabels>'
        '<userAnswer><match statementIndex="0" labelIndex="1"/></userAnswer>'
        '</likertScaleQuestion>'
    ),
    'dndQuestion': wrap_question(
        '<dndQuestion id="q-dnd" status="correct" evaluationEnabled="true">'
        '<direction><text>Drag and drop</text></direction>'
        '<objects><object id="o1">Apple</object><object id="o2">Car</object></objects>'
        '<destinations><destination id="d1">Fruit</destination><destination id="d2">Vehicle</destination></destinations>'
        '<matches><match objectIndex="0" destinationIndex="0"/><match objectIndex="1" destinationIndex="1"/></matches>'
        '<userAnswer><match objectIndex="0" destinationIndex="0"/><match objectIndex="1" destinationIndex="1"/></userAnswer>'
        '</dndQuestion>'
    ),
    'unknownQuestion': wrap_question(
        '<futureQuestion id="q-future" status="answered" evaluationEnabled="false">'
        '<direction><text>Unknown type</text></direction></futureQuestion>'
    ),
}
