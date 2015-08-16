void uhf_tx_enable(){
    pinMode(6, OUTPUT); // GND pin
    pinMode(5, OUTPUT); // VCC pin
    pinMode(4, OUTPUT); // Data pin
    digitalWrite(6, false);
    digitalWrite(5, true);
}

void uhf_tx_disable(){
    digitalWrite(5, false); // Disable VCC
}

#define UHF_BAUD_RATE 600
#define US_PER_BIT ((1000000/UHF_BAUD_RATE)/2)

void uhf_tx_bit_raw(boolean on){
    digitalWrite(4, on);
    delayMicroseconds(US_PER_BIT);
}

void uhf_tx_byte_raw(uint8_t foo){
    for(int8_t i = 7; i >= 0; i--){
        uhf_tx_bit_raw((foo >> i) & 1);
    }
}

// commands for button presses are normally sent 8 times with 0.72 ms interval (720 us)
void uhf_tx_remote_egg_frame(uint32_t data){
    uint8_t cmd[] = {data >> 16, data >> 8, data};
    // command prefix
    uhf_tx_bit_raw(1);
    uhf_tx_bit_raw(1);
    uhf_tx_bit_raw(1);
    uhf_tx_bit_raw(1);
    uhf_tx_byte_raw(0x11);
    uhf_tx_byte_raw(0x45);

    for(size_t i = 0; i < sizeof(cmd); i++){
        uhf_tx_byte_raw(cmd[i]);
    }
}

uint8_t current_pattern = 0;
uint8_t current_command = 0;
bool current_direction = true;
uint32_t commands_up[] = {0x511115, 0x454511, 0x514451};
uint32_t commands_down[] = {0x444455, 0x515511, 0x151445, 0x445151};

void remote_egg_step_up(void){
    if(!current_direction){
        current_command = 0;
    }
    current_direction = true;
    uhf_tx_remote_egg_frame(commands_up[current_command]);
    current_command++;
    current_command %= 3;
    current_pattern++;
}

void remote_egg_step_down(void){
    if(current_direction){
        current_command = 0;
    }
    current_direction = false;
    uhf_tx_remote_egg_frame(commands_down[current_command]);
    current_command++;
    current_command %= 4;
    current_pattern--;
}

#define COMMAND_TIME 50

void remote_egg_stop(void){
    uhf_tx_remote_egg_frame(0x544445);
    delay(COMMAND_TIME);
    uhf_tx_remote_egg_frame(0x551111);
    delay(COMMAND_TIME);
}

void remote_egg_go_to_pattern(uint8_t pattern){
    while(current_pattern != pattern){
        if(pattern>current_pattern){
            remote_egg_step_up();
        } else {
            remote_egg_step_down();
        }
        delay(COMMAND_TIME);
    }
    Serial.println(current_pattern);
}

void setup(){
    Serial.begin(19200);
    current_pattern = 0;
    current_command = 0;

    uhf_tx_enable();
    
    // go to pattern 20 and run it for 13 seconds
    remote_egg_go_to_pattern(20);
    for(size_t i = 0; i < 13; i++){
        delay(1000);
    }

    remote_egg_stop();
    uhf_tx_disable();
}

void loop(){
}
