<template>
    <div>
      <!-- Hero Section -->
      <section id="hero" class="relative overflow-hidden bg-gradient-to-br from-primary via-blue-700 to-indigo-800 text-white pt-24 pb-20 md:pt-32 md:pb-28">
        <!-- Subtle overlay -->
        <div class="absolute inset-0 bg-black opacity-10"></div>
        <div class="relative max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center z-10">
          <h1 class="text-4xl md:text-5xl lg:text-6xl font-bold tracking-tight mb-5">
            Stop Guessing. Start Classifying.
          </h1>
          <p class="text-lg md:text-xl text-indigo-100 mb-10 max-w-3xl mx-auto">
            Transform your messy vendor lists into actionable, NAICS-classified data in minutes, not weeks. Leverage AI for unmatched accuracy and gain deeper procurement insights.
          </p>
          <div class="flex flex-col sm:flex-row justify-center items-center space-y-4 sm:space-y-0 sm:space-x-4">
            <a href="#loginCardAnchor"
               @click.prevent="scrollToLogin"
               class="inline-block bg-white text-primary font-semibold py-3 px-8 rounded-md shadow-lg hover:bg-gray-100 transition duration-300 text-lg transform hover:scale-105">
              Get Started Now
            </a>
             <!-- Optional Secondary CTA -->
             <!--
             <a href="#features" @click.prevent="scrollToFeatures"
               class="inline-block text-white font-medium py-3 px-8 rounded-md hover:bg-white/10 transition duration-300">
              Learn More
            </a>
            -->
          </div>
        </div>
         <!-- Optional: Subtle background pattern or graphic -->
         <!-- <div class="absolute bottom-0 left-0 w-full h-32 bg-gradient-to-t from-light to-transparent"></div> -->
      </section>
  
      <!-- Logos / Social Proof (Placeholder) -->
      <section class="py-8 bg-gray-50">
          <div class="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
              <p class="text-center text-sm font-semibold text-gray-500 tracking-wider uppercase">
                  Trusted by leading procurement teams
              </p>
              <div class="mt-6 grid grid-cols-2 gap-4 md:grid-cols-4 lg:grid-cols-5 items-center">
                  <!-- Replace with actual logos -->
                  <div class="flex justify-center col-span-1"> <span class="text-gray-400 text-2xl italic">Logo Inc</span> </div>
                  <div class="flex justify-center col-span-1"> <span class="text-gray-400 text-2xl italic">VendorBase</span> </div>
                  <div class="flex justify-center col-span-1"> <span class="text-gray-400 text-2xl italic">SupplyCo</span> </div>
                  <div class="flex justify-center col-span-1"> <span class="text-gray-400 text-2xl italic">Analytics Ltd</span> </div>
                  <div class="flex justify-center col-span-1 hidden lg:flex"> <span class="text-gray-400 text-2xl italic">Insight Corp</span> </div>
              </div>
          </div>
      </section>
  
      <!-- Problem / Solution Section -->
      <section id="problem-solution" class="py-16 md:py-20">
          <div class="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 grid md:grid-cols-2 gap-12 items-center">
              <!-- Problem -->
              <div class="text-center md:text-left">
                   <span class="inline-block bg-red-100 text-red-700 text-xs font-semibold px-3 py-1 rounded-full mb-3">The Challenge</span>
                   <h2 class="text-3xl font-semibold mb-4">Manual Classification is Broken</h2>
                   <p class="text-gray-600 mb-6">
                       Spending hours manually assigning NAICS codes? Dealing with inconsistent data, costly errors, and missed insights? Your team's valuable time is wasted on tedious tasks instead of strategic sourcing.
                   </p>
                   <ul class="space-y-2 text-left text-gray-600">
                       <li class="flex items-start"><CheckCircleIcon class="h-5 w-5 text-red-500 mr-2 mt-0.5 flex-shrink-0" /><span>Time-consuming & resource-intensive</span></li>
                       <li class="flex items-start"><CheckCircleIcon class="h-5 w-5 text-red-500 mr-2 mt-0.5 flex-shrink-0" /><span>Prone to inconsistencies and errors</span></li>
                       <li class="flex items-start"><CheckCircleIcon class="h-5 w-5 text-red-500 mr-2 mt-0.5 flex-shrink-0" /><span>Leads to unreliable reporting & analytics</span></li>
                   </ul>
              </div>
               <!-- Solution -->
               <div class="text-center md:text-left bg-gradient-to-br from-blue-50 to-primary/10 p-8 rounded-lg shadow-lg border border-primary/20">
                   <span class="inline-block bg-green-100 text-green-700 text-xs font-semibold px-3 py-1 rounded-full mb-3">The Solution</span>
                   <h2 class="text-3xl font-semibold text-primary mb-4">AI-Powered Automation</h2>
                   <p class="text-gray-700 mb-6">
                       NAICS Classify uses cutting-edge AI to analyze your vendor data, perform intelligent web searches, and deliver accurate, multi-level NAICS codes automatically. Reclaim your time and unlock data potential.
                   </p>
                    <ul class="space-y-2 text-left text-gray-700">
                       <li class="flex items-start"><CheckCircleIcon class="h-5 w-5 text-green-500 mr-2 mt-0.5 flex-shrink-0" /><span>Classify thousands of vendors in minutes</span></li>
                       <li class="flex items-start"><CheckCircleIcon class="h-5 w-5 text-green-500 mr-2 mt-0.5 flex-shrink-0" /><span>Achieve >95% accuracy with AI & search</span></li>
                       <li class="flex items-start"><CheckCircleIcon class="h-5 w-5 text-green-500 mr-2 mt-0.5 flex-shrink-0" /><span>Get consistent, reliable data for insights</span></li>
                   </ul>
              </div>
          </div>
      </section>
  
      <!-- How It Works (Refined Visually) -->
      <section id="how-it-works" class="py-16 bg-gray-50">
         <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <h2 class="text-3xl font-semibold text-center mb-12">Get Results in 3 Simple Steps</h2>
            <div class="relative">
                <!-- Connecting Line (optional decorative element) -->
                 <div class="hidden md:block absolute top-1/2 left-0 w-full h-0.5 bg-gray-300 transform -translate-y-1/2 -z-1"></div>
  
                <div class="grid md:grid-cols-3 gap-8 relative">
                    <!-- Step 1 -->
                    <div class="bg-white p-6 rounded-lg shadow-lg border border-gray-200 text-center z-10">
                         <div class="relative inline-block">
                             <div class="inline-flex items-center justify-center w-16 h-16 mb-5 font-bold text-2xl text-white bg-primary rounded-full shadow-md">1</div>
                             <!-- Arrow pointing right (decorative) -->
                             <div class="hidden md:block absolute top-1/2 left-full ml-4 transform -translate-y-1/2 text-gray-300">
                                 <ArrowRightIcon class="h-8 w-8" />
                             </div>
                         </div>
                         <h4 class="text-lg font-semibold text-gray-800 mb-3">Upload Your List</h4>
                         <p class="text-sm text-gray-600">Drag & drop or select your Excel file (.xlsx/.xls) with a 'vendor_name' column. Add optional context columns for even better results.</p>
                    </div>
                     <!-- Step 2 -->
                     <div class="bg-white p-6 rounded-lg shadow-lg border border-gray-200 text-center z-10">
                        <div class="relative inline-block">
                             <div class="inline-flex items-center justify-center w-16 h-16 mb-5 font-bold text-2xl text-white bg-primary rounded-full shadow-md">2</div>
                              <!-- Arrow pointing right (decorative) -->
                             <div class="hidden md:block absolute top-1/2 left-full ml-4 transform -translate-y-1/2 text-gray-300">
                                 <ArrowRightIcon class="h-8 w-8" />
                             </div>
                         </div>
                        <h4 class="text-lg font-semibold text-gray-800 mb-3">AI Processing Magic</h4>
                        <p class="text-sm text-gray-600">Our intelligent engine analyzes names, utilizes context, performs web searches if needed, and assigns accurate NAICS codes.</p>
                     </div>
                     <!-- Step 3 -->
                     <div class="bg-white p-6 rounded-lg shadow-lg border border-gray-200 text-center z-10">
                         <div class="inline-flex items-center justify-center w-16 h-16 mb-5 font-bold text-2xl text-white bg-primary rounded-full shadow-md">3</div>
                        <h4 class="text-lg font-semibold text-gray-800 mb-3">Download Enriched Data</h4>
                        <p class="text-sm text-gray-600">Receive your original spreadsheet back, now enriched with precise Level 1-4 NAICS classifications, ready for analysis.</p>
                     </div>
                </div>
            </div>
         </div>
      </section>
  
      <!-- Features Section (Improved Layout) -->
      <section id="features" class="py-16 md:py-20">
          <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
              <h2 class="text-3xl font-semibold text-center mb-12">Powerful Features, Tangible Benefits</h2>
              <div class="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
                  <!-- Feature Card -->
                  <div class="bg-white p-6 rounded-lg shadow-md border border-gray-100 hover:shadow-lg transition duration-300">
                       <div class="flex items-center mb-3">
                           <BeakerIcon class="h-7 w-7 text-primary mr-3" />
                           <h5 class="text-lg font-semibold">Unmatched AI Accuracy</h5>
                       </div>
                       <p class="text-sm text-gray-600">Leverages advanced LLMs trained on vast datasets for industry-leading classification precision.</p>
                  </div>
                  <!-- Feature Card -->
                   <div class="bg-white p-6 rounded-lg shadow-md border border-gray-100 hover:shadow-lg transition duration-300">
                       <div class="flex items-center mb-3">
                           <MagnifyingGlassIcon class="h-7 w-7 text-primary mr-3" />
                           <h5 class="text-lg font-semibold">Intelligent Web Search</h5>
                       </div>
                       <p class="text-sm text-gray-600">Automatically researches ambiguous vendors online, filling data gaps and boosting classification rates.</p>
                  </div>
                  <!-- Feature Card -->
                   <div class="bg-white p-6 rounded-lg shadow-md border border-gray-100 hover:shadow-lg transition duration-300">
                       <div class="flex items-center mb-3">
                           <Bars4Icon class="h-7 w-7 text-primary mr-3" />
                           <h5 class="text-lg font-semibold">Multi-Level Hierarchy</h5>
                       </div>
                       <p class="text-sm text-gray-600">Provides detailed NAICS codes up to Level 4, enabling granular spend analysis and reporting.</p>
                  </div>
                   <!-- Feature Card -->
                  <div class="bg-white p-6 rounded-lg shadow-md border border-gray-100 hover:shadow-lg transition duration-300">
                       <div class="flex items-center mb-3">
                           <ArrowUpTrayIcon class="h-7 w-7 text-primary mr-3" />
                           <h5 class="text-lg font-semibold">Simple Excel Workflow</h5>
                       </div>
                       <p class="text-sm text-gray-600">Integrates seamlessly with your existing spreadsheets. Just upload, process, and download.</p>
                  </div>
                   <!-- Feature Card -->
                  <div class="bg-white p-6 rounded-lg shadow-md border border-gray-100 hover:shadow-lg transition duration-300">
                       <div class="flex items-center mb-3">
                           <ClockIcon class="h-7 w-7 text-primary mr-3" />
                           <h5 class="text-lg font-semibold">Rapid Processing</h5>
                       </div>
                       <p class="text-sm text-gray-600">Asynchronous backend handles large files quickly, freeing up your team's time immediately.</p>
                  </div>
                   <!-- Feature Card -->
                  <div class="bg-white p-6 rounded-lg shadow-md border border-gray-100 hover:shadow-lg transition duration-300">
                       <div class="flex items-center mb-3">
                           <LockClosedIcon class="h-7 w-7 text-primary mr-3" />
                           <h5 class="text-lg font-semibold">Secure & Confidential</h5>
                       </div>
                       <p class="text-sm text-gray-600">Your data is encrypted and handled with strict security protocols throughout the process.</p>
                  </div>
              </div>
          </div>
      </section>
  
       <!-- Testimonial Section (Placeholder) -->
      <section id="testimonials" class="py-16 bg-gradient-to-r from-gray-50 to-blue-50">
           <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
               <h2 class="text-3xl font-semibold mb-8">Don't Just Take Our Word For It</h2>
               <div class="relative p-8 bg-white rounded-lg shadow-xl border border-gray-200">
                   <!-- Quote Icon -->
                   <div class="absolute top-0 left-0 -mt-4 -ml-4 text-primary/20">
                       <svg class="h-16 w-16" fill="currentColor" viewBox="0 0 32 32">
                           <path d="M9.333 7h-2.667c-1.835 0-3.333 1.498-3.333 3.333v11.333c0 1.835 1.498 3.333 3.333 3.333h6.667v-8h-4v-4c0-1.102.897-2 2-2h2v-4zM25.333 7h-2.667c-1.835 0-3.333 1.498-3.333 3.333v11.333c0 1.835 1.498 3.333 3.333 3.333h6.667v-8h-4v-4c0-1.102.897-2 2-2h2v-4z" />
                       </svg>
                   </div>
                  <blockquote class="relative italic text-gray-700 text-lg">
                     "NAICS Classify saved us countless hours. What used to take a week now takes minutes, and the accuracy is fantastic. It's essential for our vendor management."
                   </blockquote>
                   <footer class="mt-6">
                       <p class="font-semibold text-gray-900">Jane Doe</p>
                       <p class="text-sm text-gray-500">Procurement Manager, Tech Solutions Inc.</p>
                   </footer>
               </div>
           </div>
      </section>
  
  
      <!-- Login Card Section -->
      <section id="loginCardAnchor" class="py-16">
          <div class="max-w-lg mx-auto px-4">
             <Login @login-successful="handleLogin" />
          </div>
      </section>
    </div>
  </template>
  
  <script setup lang="ts">
  import Login from './Login.vue';
  // Import necessary icons from Heroicons (ensure @heroicons/vue is installed)
  import {
      CheckCircleIcon,
      ArrowRightIcon,
      BeakerIcon,
      MagnifyingGlassIcon,
      Bars4Icon,
      ArrowUpTrayIcon,
      ClockIcon,
      LockClosedIcon
  } from '@heroicons/vue/24/outline'; // Using outline style
  
  const emit = defineEmits(['login-successful']);
  
  const handleLogin = () => {
    emit('login-successful');
  };
  
  // Helper for scrolling smoothly to sections
  const smoothScrollTo = (elementId: string) => {
      const element = document.getElementById(elementId);
        if (element) {
            const navbarHeight = 70; // Estimate navbar height
            const elementPosition = element.getBoundingClientRect().top;
            const offsetPosition = elementPosition + window.pageYOffset - navbarHeight;
            window.scrollTo({ top: offsetPosition, behavior: 'smooth' });
        }
  }
  
  const scrollToLogin = (event: Event) => {
        event.preventDefault();
        smoothScrollTo('loginCardAnchor');
  }
  
  // Optional: Scroll to features
  // const scrollToFeatures = (event: Event) => {
  //       event.preventDefault();
  //       smoothScrollTo('features');
  // }
  
  </script>
  
  <style scoped>
   /* Optional: Add subtle background patterns or animations if desired */
   /* Example: Subtle pattern for hero */
   /* #hero::before {
       content: '';
       position: absolute;
       inset: 0;
       background-image: url('path/to/your/subtle-pattern.svg');
       background-repeat: repeat;
       opacity: 0.05;
       z-index: 0;
   } */
  
   /* Ensure high z-index for step numbers if using lines */
   #how-it-works .relative > .grid { /* Target the grid directly inside the relative div */
       position: relative; /* Ensure grid items can be positioned relative to this */
       z-index: 10; /* Place grid items above the line */
   }
   #how-it-works .relative > .absolute { /* Target the line */
      z-index: 1; /* Place line behind grid items */
   }
  </style>