import ml_collections
import torch
import math
import numpy as np

def get_config():
  config = ml_collections.ConfigDict()

  # training
  config.training = training = ml_collections.ConfigDict()
  config.training.lightning_module = 'conditional_decreasing_variance'
  training.conditioning_approach = 'ours_slowDV' #should be converted to ours_DV for training
  training.batch_size = 16
  training.num_nodes = 1
  training.gpus = 1
  training.accelerator = None if training.gpus == 1 else 'ddp'
  training.accumulate_grad_batches = 1
  training.workers = 4*training.gpus
  #----- to be removed -----
  training.num_epochs = 10000
  training.n_iters = 500000
  training.snapshot_freq = 5000
  training.log_freq = 250
  training.eval_freq = 2500
  #------              --------
  
  training.visualization_callback = 'paired'
  training.show_evolution = False

  training.likelihood_weighting = True
  training.continuous = True
  training.reduce_mean = True 
  training.sde = 'vesde'

  # sampling
  config.sampling = sampling = ml_collections.ConfigDict()
  sampling.method = 'pc'
  sampling.predictor = 'conditional_reverse_diffusion'
  sampling.corrector = 'conditional_langevin'
  sampling.n_steps_each = 1
  sampling.noise_removal = True
  sampling.probability_flow = False
  sampling.snr = 0.15 #0.15 in VE sde (you typically need to play with this term - more details in the main paper)
  sampling.use_path = False #new. We use a specific path of the forward diffusion of the condition instead of getting new samples from the perturbation kernel p(y_t|y_0) each time.
  
  # evaluation (this file is not modified at all - subject to change)
  config.eval = evaluate = ml_collections.ConfigDict()
  evaluate.workers = 4*training.gpus

  #new settings
  evaluate.callback = 'test_paired'
  evaluate.evaluation_metrics = ['lpips', 'psnr', 'ssim', 'consistency', 'diversity']
  evaluate.predictor = 'default'
  evaluate.corrector = 'default'
  evaluate.p_steps = 'default'
  evaluate.c_steps = 'default'
  evaluate.snr = [0.15]
  evaluate.denoise = True
  evaluate.use_path = False #new. We use a specific path of the forward diffusion of the condition instead of getting new samples from the perturbation kernel p(y_t|y_0) each time.
  evaluate.draws = [1]
  evaluate.save_samples = True  
  evaluate.first_test_batch = 100
  evaluate.last_test_batch = 200
  evaluate.base_log_dir = '/home/gb511/evaluation' #'/home/gb511/rds/rds-t2-cs138-LlrDsbHU5UM/gb511/evaluation' #use the suitable logging directory for the hpc.
  

  #old settings
  evaluate.batch_size = 25

  evaluate.begin_ckpt = 50
  evaluate.end_ckpt = 96
  evaluate.enable_sampling = True
  evaluate.num_samples = 50000
  evaluate.enable_loss = True
  evaluate.enable_bpd = False
  evaluate.bpd_dataset = 'test'

  # data
  config.data = data = ml_collections.ConfigDict()
  data.base_dir = 'datasets' #'/home/gb511/rds/rds-t2-cs138-LlrDsbHU5UM/gb511/datasets'
  data.dataset = 'celebA-HQ-160'
  data.task = 'super-resolution'
  data.scale = 8
  data.mask_coverage = 0.25
  data.use_data_mean = False
  data.datamodule = 'LRHR_PKLDataset'
  data.create_dataset = False
  data.split = [0.8, 0.1, 0.1]
  data.target_resolution = 160
  data.image_size = 160
  data.effective_image_size = data.image_size
  data.shape_x = [3, data.image_size, data.image_size]
  data.shape_y = [3, data.image_size, data.image_size]
  data.centered = False
  data.use_flip = True
  data.use_crop = False
  data.use_rot = False
  data.upscale_lr = True
  data.uniform_dequantization = False
  data.num_channels = data.shape_x[0]+data.shape_y[0] #the number of channels the model sees as input.

  # model
  config.model = model = ml_collections.ConfigDict()
  model.checkpoint_path = '/home/gb511/saved_checkpoints/checkpoints/super-resolution/celebA-HQ-160/ours_slowDV/epoch=87-step=447654.ckpt'
  model.num_scales = 1000

  #SIGMA INFORMATION FOR THE VE SDE
  model.reach_target_steps = 500000
  model.sigma_max_x = np.sqrt(np.prod(data.shape_x))
  model.sigma_max_y = np.sqrt(np.prod(data.shape_y))
  model.sigma_max_y_target = 1
  model.sigma_min_x = 5e-3
  model.sigma_min_y = 5e-3
  model.sigma_min_y_target = 5e-3

  model.beta_min = 0.1
  model.beta_max = 20.

  model.dropout = 0.1
  model.embedding_type = 'positional'


  model.name = 'ddpm_paired'
  model.scale_by_sigma = True
  model.ema_rate = 0.999
  model.normalization = 'GroupNorm'
  model.nonlinearity = 'swish'
  model.nf = 96
  model.ch_mult = (1, 1, 2, 2, 3, 3)
  model.num_res_blocks = 2
  model.attn_resolutions = (20, 10, 5)
  model.resamp_with_conv = True
  model.conditional = True
  model.fir = True
  model.fir_kernel = [1, 3, 3, 1]
  model.skip_rescale = True
  model.resblock_type = 'biggan'
  model.progressive = 'output_skip'
  model.progressive_input = 'input_skip'
  model.progressive_combine = 'sum'
  model.attention_type = 'ddpm'
  model.init_scale = 0.
  model.fourier_scale = 16
  model.conv_size = 3
  model.input_channels = data.num_channels
  model.output_channels = data.num_channels


  # optimization
  config.optim = optim = ml_collections.ConfigDict()

  optim.weight_decay = 0
  optim.optimizer = 'Adam'
  optim.lr = 2e-4
  optim.beta1 = 0.9
  optim.eps = 1e-8
  optim.warmup = 2500 #set it to 0 if you do not want to use warm up.
  optim.grad_clip = 1 #set it to 0 if you do not want to use gradient clipping using the norm algorithm. Gradient clipping defaults to the norm algorithm.

  config.seed = 42

  return config