#include "feat/wave-reader.h"
#include "online2/online-feature-pipeline.h"
#include "online2/online-gmm-decoding.h"
#include "online2/onlinebin-util.h"
#include "online2/online-timing.h"
#include "online2/online-endpoint.h"
#include "fstext/fstext-lib.h"
#include "lat/lattice-functions.h"

namespace kaldi {
    std::string get_transcription(const fst::SymbolTable *word_syms,
                                  const CompactLattice &clat) {
        if (clat.NumStates() == 0) {
            KALDI_WARN << "Empty lattice.";
            return "";
        }

        CompactLattice best_path_clat;
        CompactLatticeShortestPath(clat, &best_path_clat);

        Lattice best_path_lat;
        ConvertLattice(best_path_clat, &best_path_lat);

        LatticeWeight weight;
        std::vector<int32> alignment;
        std::vector<int32> words;
        GetLinearSymbolSequence(best_path_lat, &alignment, &words, &weight);

        std::string result = "";
        for (size_t i = 0; i < words.size(); ++i) {
            if (i != 0)
                result += " ";
            result += word_syms->Find(words[i]);
        }
        return result;
    }
}

int main(int argc, char *argv[]) {
    try {
        using namespace kaldi;
        using namespace fst;

        typedef kaldi::int32 int32;
        typedef kaldi::int64 int64;

        const char *usage =
            "Reads in wav file(s) and simulates online decoding, including\n"
            "basis-fMLLR adaptation and endpointing. Writes lattices.\n"
            "Models are specified via options.\n"
            "\n"
            "Usage: file-decoder [options] <fst-in> "
            "<word-syms-in> <wav-rspecifier>\n";

        ParseOptions po(usage);
        OnlineFeaturePipelineCommandLineConfig feature_cmdline_config;
        feature_cmdline_config.Register(&po);
        OnlineEndpointConfig endpoint_config;
        endpoint_config.Register(&po);
        OnlineGmmDecodingConfig decode_config;
        decode_config.Register(&po);
        BaseFloat chunk_length_secs = 0.05;
        po.Register("chunk-length", &chunk_length_secs,
                    "Length of chunk size in seconds, that we process.");
        po.Read(argc, argv);

        if (po.NumArgs() != 3) {
            po.PrintUsage();
            return 1;
        }

        std::string word_syms_rxfilename = po.GetArg(1),
                    fst_rxfilename = po.GetArg(2),
                    wav_rspecifier = po.GetArg(3);

        OnlineFeaturePipelineConfig feature_config(feature_cmdline_config);
        OnlineFeaturePipeline pipeline_prototype(feature_config);
        OnlineGmmDecodingModels gmm_models(decode_config);

        fst::SymbolTable *word_syms = fst::SymbolTable::ReadText(word_syms_rxfilename);
        fst::Fst<fst::StdArc> *decode_fst = ReadFstKaldiGeneric(fst_rxfilename);
        Input wav_reader(wav_rspecifier);

        uint32 chunk_size = 1024;
        char *buffer = new char[chunk_size];
        BaseFloat samp_freq = 16000;
        int32 num_done = 0;
        OnlineGmmAdaptationState adaptation_state;
        SingleUtteranceGmmDecoder *decoder = new SingleUtteranceGmmDecoder(decode_config,
                                                                           gmm_models,
                                                                           pipeline_prototype,
                                                                           *decode_fst,
                                                                           adaptation_state);

        while (wav_reader.IsOpen()) {
            wav_reader.Stream().read(buffer, 1024);
            Vector<BaseFloat> wave_part(512);
            uint16 *data_ptr = reinterpret_cast<uint16*>(buffer);
            for (int i = 0; i < 512; ++i) {
                int16 k = *data_ptr++;
                wave_part(i) = k;
            }
            decoder->FeaturePipeline().AcceptWaveform(samp_freq, wave_part);
            decoder->AdvanceDecoding();

            if (decoder->EndpointDetected(endpoint_config)) {
                decoder->FinalizeDecoding();
                bool end_of_utterance = true;
                decoder->EstimateFmllr(end_of_utterance);
                CompactLattice clat;
                bool rescore_if_needed = true;
                decoder->GetLattice(rescore_if_needed, end_of_utterance, &clat);
                std::string transcription = get_transcription(word_syms, clat);
                std::cout << transcription << std::endl;

                // In an application you might avoid updating the adaptation state if
                // you felt the utterance had low confidence.    See lat/confidence.h
                decoder->GetAdaptationState(&adaptation_state);
                delete decoder;
                decoder = new SingleUtteranceGmmDecoder(decode_config,
                                                        gmm_models,
                                                        pipeline_prototype,
                                                        *decode_fst,
                                                        adaptation_state);
                ++num_done;
            }
        }

        delete word_syms;
        delete decode_fst;
        return (num_done != 0 ? 0 : 1);
    } catch(const std::exception& e) {
        std::cerr << e.what();
        return -1;
    }
}
