var player = document.getElementById('player');

var handleSuccess = function(stream) {
    var bufferSize = 1024;
    var inputChannels = 1;
    var outputChannels = 1;

    var context = new AudioContext();
    var source = context.createMediaStreamSource(stream);
    var processor = context.createScriptProcessor(bufferSize, inputChannels, outputChannels);

    source.connect(processor);
    processor.connect(context.destination);

    processor.onaudioprocess = function(e) {
        // Do something with the data, i.e Convert this to WAV
        console.log(e.inputBuffer);
    };
};

navigator.mediaDevices.getUserMedia({ audio: true, video: false })
    .then(handleSuccess);
