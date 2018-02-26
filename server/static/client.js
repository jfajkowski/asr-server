var context = new (window.AudioContext || window.webkitAudioContext)();
var bufferSize = 4096;
var hypothesesBox = document.getElementById('hypotheses');
var clearButton = document.getElementById('clear');

var client = {};
client.connect = function()  {
    var ws = new WebSocket('wss://localhost:10000/websocket');

    ws.onopen = function() {
        console.log('ws connected');
        client.ws = ws;
    };

    ws.onerror = function() {
        console.log('ws error');
    };

    ws.onclose = function() {
        console.log('ws closed');
    };

    ws.onmessage = function(msgevent) {
        var hypothesis = msgevent.data;
        hypothesesBox.innerHTML += '<p>' + hypothesis + '</p>';
    };
};

client.send = function(frames) {
    if (!this.ws) {
        console.log('no connection');
        return;
    }
    this.ws.send(frames);
};

context.createSpeechRecognition = function() {
    if (!context.createScriptProcessor) {
        node = context.createJavaScriptNode(bufferSize, 1, 1);
    } else {
        node = context.createScriptProcessor(bufferSize, 1, 1);
    }
    var resize = function(inputBuffer) {
        var l = inputBuffer.length;
        var outputBuffer = new Int16Array(l);

        while (l--) {
            outputBuffer[l] = inputBuffer[l] * 32768;
        }

        return outputBuffer;
    };
    var resampler = new Resampler(44100, 16000, 1, bufferSize);


    node.onaudioprocess = function(e) {
        var input = e.inputBuffer.getChannelData(0);
        var output = e.outputBuffer.getChannelData(0);
        var resampled = resampler.resampler(input);
        var resized = resize(resampled);
        client.send(resized.buffer);

        for (var i = 0; i < bufferSize; i++) {
            output[i] = input[i];
        }
    }
    return node;
};

var handleSuccess = function(stream) {
    var source = context.createMediaStreamSource(stream);
    var gainNode = context.createGain();
    var speechRecognitionNode = context.createSpeechRecognition();

    gainNode.gain.value = 0.1;

    source.connect(gainNode);
    gainNode.connect(speechRecognitionNode);
    speechRecognitionNode.connect(context.destination);
};

clearButton.onclick = function() {
    hypothesesBox.innerHTML = '';
}

client.connect();
navigator.mediaDevices.getUserMedia({ audio: true, video: false }).then(handleSuccess);
