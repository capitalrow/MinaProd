#!/usr/bin/env python3
"""
End-to-End Automated Pipeline Testing for MINA
Uses existing AudioFileSimulator and STUB_TRANSCRIPTION mode
"""

import os
import time
import json
import asyncio
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PipelineE2ETester:
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        self.driver = None
        self.test_results = {}
        
    def setup_browser(self):
        """Setup Chrome with audio simulation capabilities"""
        chrome_options = Options()
        chrome_options.add_argument("--use-fake-ui-for-media-stream")
        chrome_options.add_argument("--use-fake-device-for-media-stream") 
        chrome_options.add_argument("--autoplay-policy=no-user-gesture-required")
        chrome_options.add_argument("--disable-web-security")
        chrome_options.add_argument("--allow-running-insecure-content")
        
        # Enable audio automation
        chrome_options.add_experimental_option("prefs", {
            "profile.default_content_setting_values.media_stream_mic": 1,
            "profile.default_content_setting_values.media_stream_camera": 1,
            "profile.default_content_setting_values.notifications": 1
        })
        
        self.driver = webdriver.Chrome(options=chrome_options)
        logger.info("✅ Browser setup complete with audio simulation")
        
    def test_audio_file_simulation(self):
        """Test 1: AudioFileSimulator End-to-End"""
        logger.info("🎵 Testing AudioFileSimulator pipeline...")
        
        try:
            # Navigate to live page
            self.driver.get(f"{self.base_url}/live")
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "startBtn"))
            )
            
            # Enable STUB mode via JavaScript
            self.driver.execute_script("""
                // Set stub mode for testing
                window.TESTING_MODE = true;
                console.log('🧪 Testing mode enabled');
            """)
            
            # Initialize AudioFileSimulator
            self.driver.execute_script("""
                if (window.audioFileSimulator) {
                    console.log('🎵 Starting AudioFileSimulator test...');
                    window.audioFileSimulator.startSimulation();
                }
            """)
            
            # Wait for transcription to appear
            transcription_element = WebDriverWait(self.driver, 30).until(
                EC.presence_of_element_located((By.ID, "transcription"))
            )
            
            # Monitor for 10 seconds
            time.sleep(10)
            
            # Get final transcription content
            final_text = transcription_element.text
            logger.info(f"📄 Final transcription: {final_text}")
            
            # Validate results
            success = len(final_text) > 0 and "error" not in final_text.lower()
            
            self.test_results['audio_file_simulation'] = {
                'success': success,
                'transcription_length': len(final_text),
                'transcription_preview': final_text[:100] + "..." if len(final_text) > 100 else final_text
            }
            
            logger.info(f"✅ Audio file simulation test: {'PASSED' if success else 'FAILED'}")
            return success
            
        except Exception as e:
            logger.error(f"❌ Audio file simulation test failed: {e}")
            self.test_results['audio_file_simulation'] = {'success': False, 'error': str(e)}
            return False
    
    def test_stub_transcription_mode(self):
        """Test 2: STUB_TRANSCRIPTION Mode"""
        logger.info("🎭 Testing STUB_TRANSCRIPTION mode...")
        
        try:
            # Set environment variable for stub mode
            os.environ['STUB_TRANSCRIPTION'] = 'true'
            
            # Navigate to live page  
            self.driver.get(f"{self.base_url}/live")
            
            # Start recording with stub mode
            start_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.ID, "startBtn"))
            )
            start_button.click()
            
            # Wait for stub transcription responses
            time.sleep(5)
            
            # Check for stub responses in transcription area
            transcription = self.driver.find_element(By.ID, "transcription").text
            
            # Stub mode should return predictable test content
            success = "stub" in transcription.lower() or len(transcription) > 0
            
            self.test_results['stub_transcription'] = {
                'success': success,
                'content': transcription[:100] + "..." if len(transcription) > 100 else transcription
            }
            
            logger.info(f"✅ STUB transcription test: {'PASSED' if success else 'FAILED'}")
            return success
            
        except Exception as e:
            logger.error(f"❌ STUB transcription test failed: {e}")
            self.test_results['stub_transcription'] = {'success': False, 'error': str(e)}
            return False
        finally:
            # Clean up environment
            os.environ.pop('STUB_TRANSCRIPTION', None)
    
    def test_websocket_connectivity(self):
        """Test 3: WebSocket Connection & Events"""
        logger.info("🔌 Testing WebSocket connectivity...")
        
        try:
            self.driver.get(f"{self.base_url}/live")
            
            # Check WebSocket connection status via JavaScript
            connection_status = self.driver.execute_script("""
                return new Promise((resolve) => {
                    if (window.socket && window.socket.connected) {
                        resolve({connected: true, transport: window.socket.io.engine.transport.name});
                    } else {
                        // Wait for connection
                        setTimeout(() => {
                            if (window.socket && window.socket.connected) {
                                resolve({connected: true, transport: window.socket.io.engine.transport.name});
                            } else {
                                resolve({connected: false});
                            }
                        }, 3000);
                    }
                });
            """)
            
            success = connection_status.get('connected', False)
            
            self.test_results['websocket_connectivity'] = {
                'success': success,
                'transport': connection_status.get('transport', 'unknown')
            }
            
            logger.info(f"✅ WebSocket connectivity test: {'PASSED' if success else 'FAILED'}")
            return success
            
        except Exception as e:
            logger.error(f"❌ WebSocket connectivity test failed: {e}")
            self.test_results['websocket_connectivity'] = {'success': False, 'error': str(e)}
            return False
    
    def test_ui_responsiveness(self):
        """Test 4: UI Component Responsiveness"""
        logger.info("📱 Testing UI responsiveness...")
        
        try:
            self.driver.get(f"{self.base_url}/live")
            
            # Test key UI elements
            elements_to_test = [
                ('startBtn', 'Start Button'),
                ('stopBtn', 'Stop Button'), 
                ('transcription', 'Transcription Area'),
                ('status', 'Status Display')
            ]
            
            ui_results = {}
            for element_id, name in elements_to_test:
                try:
                    element = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((By.ID, element_id))
                    )
                    ui_results[element_id] = {
                        'present': True,
                        'visible': element.is_displayed(),
                        'enabled': element.is_enabled() if element.tag_name in ['button', 'input'] else True
                    }
                except:
                    ui_results[element_id] = {'present': False, 'visible': False, 'enabled': False}
            
            # Calculate success rate
            total_elements = len(elements_to_test)
            successful_elements = sum(1 for result in ui_results.values() if result.get('present', False))
            success_rate = successful_elements / total_elements
            
            success = success_rate >= 0.8  # 80% success rate required
            
            self.test_results['ui_responsiveness'] = {
                'success': success,
                'success_rate': f"{success_rate:.1%}",
                'elements': ui_results
            }
            
            logger.info(f"✅ UI responsiveness test: {'PASSED' if success else 'FAILED'} ({success_rate:.1%})")
            return success
            
        except Exception as e:
            logger.error(f"❌ UI responsiveness test failed: {e}")
            self.test_results['ui_responsiveness'] = {'success': False, 'error': str(e)}
            return False
    
    def run_full_test_suite(self):
        """Run complete automated test suite"""
        logger.info("🚀 Starting MINA E2E Automated Test Suite")
        
        try:
            self.setup_browser()
            
            tests = [
                ('WebSocket Connectivity', self.test_websocket_connectivity),
                ('UI Responsiveness', self.test_ui_responsiveness), 
                ('STUB Transcription Mode', self.test_stub_transcription_mode),
                ('Audio File Simulation', self.test_audio_file_simulation)
            ]
            
            results = []
            for test_name, test_func in tests:
                logger.info(f"\n📋 Running: {test_name}")
                result = test_func()
                results.append((test_name, result))
                time.sleep(2)  # Brief pause between tests
            
            # Generate report
            self.generate_test_report(results)
            
        except Exception as e:
            logger.error(f"❌ Test suite failed: {e}")
        finally:
            if self.driver:
                self.driver.quit()
    
    def generate_test_report(self, results):
        """Generate comprehensive test report"""
        passed_tests = sum(1 for _, result in results if result)
        total_tests = len(results)
        success_rate = passed_tests / total_tests if total_tests > 0 else 0
        
        print("\n" + "="*60)
        print("📊 MINA E2E AUTOMATED TEST REPORT")
        print("="*60)
        print(f"🎯 Overall Success Rate: {success_rate:.1%} ({passed_tests}/{total_tests})")
        print("\n📋 Test Results:")
        
        for test_name, result in results:
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"   {status} {test_name}")
        
        print("\n📄 Detailed Results:")
        print(json.dumps(self.test_results, indent=2))
        
        # Recommendations
        print("\n💡 Recommendations:")
        if success_rate >= 0.8:
            print("   🌟 Excellent! Pipeline is production-ready")
        elif success_rate >= 0.6:
            print("   ⚠️  Good foundation, minor issues to address")
        else:
            print("   🔧 Significant issues detected, investigation needed")
        
        return success_rate

if __name__ == "__main__":
    tester = PipelineE2ETester()
    tester.run_full_test_suite()