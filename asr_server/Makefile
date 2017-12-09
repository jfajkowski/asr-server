KALDI_DIR = /opt/kaldi

all:

include $(KALDI_DIR)/src/kaldi.mk
CXXFLAGS += -I $(KALDI_DIR)/src

LDFLAGS += $(CUDA_LDFLAGS)
LDLIBS += $(CUDA_LDLIBS)

BINFILES = kaldi-gmm-live-decoder

OBJFILES =

TESTFILES =

ADDLIBS = $(KALDI_DIR)/src/online2/kaldi-online2.a       \
          $(KALDI_DIR)/src/ivector/kaldi-ivector.a       \
          $(KALDI_DIR)/src/nnet3/kaldi-nnet3.a           \
          $(KALDI_DIR)/src/chain/kaldi-chain.a           \
          $(KALDI_DIR)/src/nnet2/kaldi-nnet2.a           \
          $(KALDI_DIR)/src/cudamatrix/kaldi-cudamatrix.a \
          $(KALDI_DIR)/src/decoder/kaldi-decoder.a       \
          $(KALDI_DIR)/src/lat/kaldi-lat.a               \
          $(KALDI_DIR)/src/fstext/kaldi-fstext.a         \
          $(KALDI_DIR)/src/hmm/kaldi-hmm.a               \
          $(KALDI_DIR)/src/feat/kaldi-feat.a             \
          $(KALDI_DIR)/src/transform/kaldi-transform.a   \
          $(KALDI_DIR)/src/gmm/kaldi-gmm.a               \
          $(KALDI_DIR)/src/tree/kaldi-tree.a             \
          $(KALDI_DIR)/src/util/kaldi-util.a             \
          $(KALDI_DIR)/src/matrix/kaldi-matrix.a         \
          $(KALDI_DIR)/src/base/kaldi-base.a 
include $(KALDI_DIR)/src/makefiles/default_rules.mk
