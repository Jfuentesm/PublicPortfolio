<template>
    <div>
      <!-- Hero Section (Full Width) -->
      <section id="hero">
        <div class="container">
          <h1 class="display-4 mb-3">Automate Vendor Classification</h1>
          <p class="lead mb-4">Effortlessly classify your vendors using NAICS codes with our powerful AI-driven tool. Save time, ensure accuracy, and gain valuable insights.</p>
          <a href="#loginCardAnchor" class="btn btn-light btn-lg" @click.prevent="scrollToLogin">Login to Get Started</a>
        </div>
      </section>

      <!-- How It Works Section (Contained Width) -->
      <section id="how-it-works">
         <div class="container">
            <h2 class="text-center mb-5">Simple Steps to Accurate Classification</h2>
            <div class="row text-center g-4 justify-content-center">
                <!-- Step 1 -->
                <div class="col-md-6 col-lg-4 d-flex align-items-stretch">
                     <div class="step-card w-100">
                        <div class="feature-icon mb-3">1</div>
                        <h4>Upload Your Data</h4>
                        <p class="text-muted">Simply upload your vendor list as an Excel file (.xlsx or .xls) containing a 'vendor_name' column. Optional columns like address, website, or examples provide additional context for higher accuracy.</p>
                    </div>
                </div>
                 <!-- Step 2 -->
                <div class="col-md-6 col-lg-4 d-flex align-items-stretch">
                    <div class="step-card w-100">
                        <div class="feature-icon mb-3">2</div>
                        <h4>AI-Powered Processing</h4>
                        <p class="text-muted">Our system leverages advanced AI and targeted web searches to accurately classify each vendor based on the official NAICS taxonomy.</p>
                    </div>
                </div>
                 <!-- Step 3 -->
                <div class="col-md-6 col-lg-4 d-flex align-items-stretch">
                     <div class="step-card w-100">
                        <div class="feature-icon mb-3">3</div>
                        <h4>Download Results</h4>
                        <p class="text-muted">Receive a detailed Excel file with your original data enriched with corresponding NAICS codes across all relevant levels (up to Level 4).</p>
                    </div>
                </div>
            </div>
         </div>
      </section>

      <!-- Features Section (Contained Width, Light Background) -->
      <section id="features" class="section-bg-light">
          <div class="container">
              <h2 class="text-center mb-5">Key Features</h2>
              <div class="row g-4">
                  <!-- Feature 1 -->
                  <div class="col-md-6">
                      <div class="card h-100">
                          <div class="card-body">
                               <div class="feature-icon-small"> <!-- Optional Icon -->
                                  <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" fill="currentColor" class="bi bi-check2-circle" viewBox="0 0 16 16">
                                      <path d="M2.5 8a5.5 5.5 0 0 1 8.25-4.764.5.5 0 0 0 .5-.866A6.5 6.5 0 1 0 14.5 8a.5.5 0 0 0-1 0 5.5 5.5 0 1 1-11 0"/>
                                      <path d="M15.354 3.354a.5.5 0 0 0-.708-.708L8 9.293 5.354 6.646a.5.5 0 1 0-.708.708l3 3a.5.5 0 0 0 .708 0z"/>
                                  </svg>
                              </div>
                              <h5 class="card-title">Accurate Classification</h5>
                              <p class="card-text">Utilizes state-of-the-art Large Language Models (LLMs) for precise NAICS code assignment, minimizing manual errors.</p>
                          </div>
                      </div>
                  </div>
                   <!-- Feature 2 -->
                  <div class="col-md-6">
                      <div class="card h-100">
                          <div class="card-body">
                               <div class="feature-icon-small">
                                  <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" fill="currentColor" class="bi bi-diagram-3" viewBox="0 0 16 16">
                                      <path fill-rule="evenodd" d="M6 3.5A1.5 1.5 0 0 1 7.5 2h1A1.5 1.5 0 0 1 10 3.5v1A1.5 1.5 0 0 1 8.5 6v1H14a.5.5 0 0 1 .5.5v1a.5.5 0 0 1-1 0V8h-5v.5a.5.5 0 0 1-1 0V8h-5v.5a.5.5 0 0 1-1 0v-1A.5.5 0 0 1 2 7h5.5V6A1.5 1.5 0 0 1 6 4.5zM8.5 7H14v1h-5.5zM2 8h5.5v1H2zm9.5 4.5a1.5 1.5 0 0 0-1.5-1.5h-1a1.5 1.5 0 0 0-1.5 1.5v1a1.5 1.5 0 0 0 1.5 1.5h1a1.5 1.5 0 0 0 1.5-1.5zm-1.5 2.5a.5.5 0 0 1-.5.5h-1a.5.5 0 0 1-.5-.5v-1a.5.5 0 0 1 .5-.5h1a.5.5 0 0 1 .5.5zM2 12.5a.5.5 0 0 1 .5-.5h1a.5.5 0 0 1 .5.5v1a.5.5 0 0 1-.5.5h-1a.5.5 0 0 1-.5-.5zM11 12.5a.5.5 0 0 1 .5-.5h1a.5.5 0 0 1 .5.5v1a.5.5 0 0 1-.5.5h-1a.5.5 0 0 1-.5-.5z"/>
                                  </svg>
                              </div>
                              <h5 class="card-title">Hierarchical Detail</h5>
                              <p class="card-text">Provides classification across all 4 levels of the NAICS taxonomy, offering granular insights into your vendor base.</p>
                          </div>
                      </div>
                  </div>
                   <!-- Feature 3 -->
                  <div class="col-md-6">
                          <div class="card h-100">
                          <div class="card-body">
                               <div class="feature-icon-small">
                                   <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" fill="currentColor" class="bi bi-search" viewBox="0 0 16 16">
                                       <path d="M11.742 10.344a6.5 6.5 0 1 0-1.397 1.398h-.001q.044.06.098.115l3.85 3.85a1 1 0 0 0 1.415-1.414l-3.85-3.85a1 1 0 0 0-.115-.1zM12 6.5a5.5 5.5 0 1 1-11 0 5.5 5.5 0 0 1 11 0"/>
                                   </svg>
                              </div>
                              <h5 class="card-title">Intelligent Search</h5>
                              <p class="card-text">Automatically researches vendors with insufficient initial data using targeted web searches, significantly improving coverage.</p>
                          </div>
                      </div>
                  </div>
                   <!-- Feature 4 -->
                  <div class="col-md-6">
                          <div class="card h-100">
                          <div class="card-body">
                               <div class="feature-icon-small">
                                  <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" fill="currentColor" class="bi bi-shield-lock" viewBox="0 0 16 16">
                                    <path d="M5.338 1.59a61 61 0 0 0-2.837.856.48.48 0 0 0-.328.39c-.554 4.157.726 7.19 2.253 9.188a10.7 10.7 0 0 0 2.287 2.233c.346.244.652.42.893.533q.18.085.293.118a1 1 0 0 0 .101.025 1 1 0 0 0 .1-.025q.114-.034.294-.118c.24-.113.547-.29.893-.533a10.7 10.7 0 0 0 2.287-2.233c1.527-1.997 2.807-5.031 2.253-9.188a.48.48 0 0 0-.328-.39c-.651-.213-1.75-.56-2.837-.855C9.552 1.29 8.5 1 8 1s-1.552.29-2.662.59zM10.823 1.073c.627.167 1.418.403 2.147.692C13.686 1.995 14 2.36 14 2.768c.506 3.787-1.084 6.487-2.368 8.258A9.7 9.7 0 0 1 8.974 12.7a1 1 0 0 1-.948 0 9.7 9.7 0 0 1-2.657-1.674C3.838 9.255 2.249 6.555 2.754 2.768c0-.407.314-.773.933-.973.729-.289 1.52-.525 2.147-.692A51 51 0 0 1 8 0c.83 0 1.89.145 2.823 1.073M9 6.5a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1 1 1 0 0 1 1 1v1.5a1 1 0 0 1-1 1h-1z"/>
                                    <path d="M6.5 10.5a1.5 1.5 0 1 1 3 0v1.5a.5.5 0 0 1-1 0V12a.5.5 0 0 1-1 0v- .5a1.5 1.5 0 0 1-3 0V10.5"/>
                                  </svg>
                              </div>
                              <h5 class="card-title">Efficient & Secure</h5>
                              <p class="card-text">Fast processing of large files via an asynchronous backend. Your data is handled securely throughout the process.</p>
                          </div>
                      </div>
                  </div>
              </div>
          </div>
      </section>

      <!-- Login Card Section (Contained Width) -->
      <section id="loginCardAnchor">
          <div class="container">
              <div class="row">
                  <!-- Centered Login Card -->
                  <div class="col-md-8 col-lg-6 mx-auto">
                     <Login @login-successful="handleLogin" />
                  </div>
              </div>
          </div>
      </section>
    </div>
  </template>

  <script setup lang="ts">
  import Login from './Login.vue';

  const emit = defineEmits(['login-successful']);

  const handleLogin = () => {
    // Forward the event up to App.vue
    emit('login-successful');
  };

  const scrollToLogin = (event: Event) => {
      event.preventDefault(); // Prevent default anchor jump
      const loginElement = document.getElementById('loginCardAnchor');
      if (loginElement) {
          loginElement.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
  }
  </script>

  <style scoped>
  /* Scoped styles specific to LandingPage if needed */
  /* Uses global styles from assets/styles.css */
  </style>