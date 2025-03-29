<template>
    <div>
      <!-- Hero Section -->
      <section id="hero" class="text-center py-5 bg-light mb-4 rounded">
        <h1 class="display-4">Automate Vendor Classification</h1>
        <p class="lead">Effortlessly classify your vendors using NAICS codes with our powerful AI-driven tool.</p>
        <p>Save time, ensure accuracy, and gain valuable insights.</p>
        <a href="#loginCardAnchor" class="btn btn-primary btn-lg mt-3">Login or Get Started</a>
      </section>
  
      <!-- How It Works Section -->
      <section id="how-it-works" class="py-5">
         <h2 class="text-center mb-4">How It Works</h2>
          <div class="row text-center">
              <div class="col-md-4 mb-3">
                  <div class="feature-icon mb-3">1</div>
                  <h4>Upload Your Data</h4>
                  <p>Simply upload your vendor list as an Excel file (.xlsx or .xls) containing a 'vendor_name' column. Other optional columns like address, website, or examples can provide additional context.</p>
              </div>
              <div class="col-md-4 mb-3">
                  <div class="feature-icon mb-3">2</div>
                  <h4>AI Classification</h4>
                  <p>Our system uses advanced AI and web search to accurately classify each vendor based on the NAICS taxonomy.</p>
              </div>
              <div class="col-md-4 mb-3">
                  <div class="feature-icon mb-3">3</div>
                  <h4>Download Results</h4>
                  <p>Receive a detailed Excel file with vendor names mapped to their corresponding NAICS codes across all levels.</p>
              </div>
          </div>
      </section>
  
      <!-- Features Section -->
      <section id="features" class="py-5 bg-light rounded">
          <h2 class="text-center mb-4">Key Features</h2>
          <div class="row">
              <div class="col-md-6 mb-3">
                  <div class="card h-100">
                      <div class="card-body">
                          <h5 class="card-title">Accurate Classification</h5>
                          <p class="card-text">Leverages Large Language Models (LLMs) for precise NAICS code assignment.</p>
                      </div>
                  </div>
              </div>
              <div class="col-md-6 mb-3">
                  <div class="card h-100">
                      <div class="card-body">
                          <h5 class="card-title">Hierarchical Detail</h5>
                          <p class="card-text">Provides classification across all 4 levels of the NAICS taxonomy.</p>
                      </div>
                  </div>
              </div>
              <div class="col-md-6 mb-3">
                      <div class="card h-100">
                      <div class="card-body">
                          <h5 class="card-title">Intelligent Search</h5>
                          <p class="card-text">Automatically researches unknown vendors using web search for better results.</p>
                      </div>
                  </div>
              </div>
              <div class="col-md-6 mb-3">
                      <div class="card h-100">
                      <div class="card-body">
                          <h5 class="card-title">Simple Workflow</h5>
                          <p class="card-text">Easy upload/download process via a user-friendly interface.</p>
                      </div>
                  </div>
              </div>
          </div>
      </section>
  
      <!-- Login Card -->
      <div id="loginCardAnchor" class="mt-5"> <!-- Anchor point -->
          <Login @login-successful="handleLogin" />
      </div>
    </div>
  </template>
  
  <script setup lang="ts">
  import Login from './Login.vue';
  
  const emit = defineEmits(['login-successful']);
  
  const handleLogin = () => {
    // Forward the event up to App.vue
    emit('login-successful');
  };
  </script>
  
  <style scoped>
  /* Styles from styles.css relevant to landing page sections */
  #hero {
      background-color: #e9ecef;
      border-radius: 10px;
      padding: 4rem 1rem;
  }
  
  .feature-icon {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      width: 4rem;
      height: 4rem;
      margin-bottom: 1rem;
      font-size: 1.5rem;
      color: #fff;
      background-color: #0d6efd;
      border-radius: 50%;
  }
  
  #features .card {
      border: 1px solid #dee2e6;
  }
  .card {
      border: none;
      border-radius: 10px;
      box-shadow: 0 4px 8px rgba(0, 0, 0, 0.05);
  }
  </style>