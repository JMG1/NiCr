/*
    NiCr Arduino Firmware V0.1

#***************************************************************************
#*   (c) Javier Martínez García 2016                                       *
#*                                                                         *
#*   This program is free software; you can redistribute it and/or modify  *
#*   it under the terms of the GNU General Public License (GPL)            *
#*   as published by the Free Software Foundation; either version 2 of     *
#*   the License, or (at your option) any later version.                   *
#*   for detail see the LICENCE text file.                                 *
#*                                                                         *
#*   This program is distributed in the hope that it will be useful,       *
#*   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
#*   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
#*   GNU Lesser General Public License for more details.                   *
#*                                                                         *
#*   You should have received a copy of the GNU Library General Public     *
#*   License along with FreeCAD; if not, write to the Free Software        *
#*   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  *
#*   USA                                                                   *
#*                                                                         *
#***************************************************************************

Current Firmware Features: -----------------------------------------------------
-SYNCHRONOUS MOVEMENT FOR 4 STEPPER MOTORS (TWO CORE XY WORKPLANES)
-DIRECT INSTRUCTION FEED BY SERIAL PORT
-WIRE TEMPERATURE SET BY INSTRUCTION

TODO List:
-LIMIT SWITCHES
-HALT BUTTON
-LCD SCREEN WITH CURRENT POSITION, INSTRUCTION, SPEED, TEMPERATURE, % AND TIME
TO COMPLETITION
-FEED SPEED SET BY INSTRUCTION AND LCD POTENTIOMETER
-WIRE TEMPERATURE SET BY LCD POTENTIOMETER
-INSTRUCTION FEED FROM SD CARD
------------------------------------------------------------------------------*/


// STEPPER MOTOR SCALE
const float scaleMA = 2.0; // (steps/mm)
const float scaleMB = 2.0; // (steps/mm)
const float scaleMC = 2.0; // (steps/mm)
const float scaleMD = 2.0; // (steps/mm)

// PINOUT --------------------------------------------------------------- PINOUT
/* POWER SOURCE PINOUT
PC PSU triggered to ON when pin goes LOW
*/
const int PIN_PSU_POWER = 0;

/*
 * WIRE
 */
const int PIN_WIRE = 0;
int wire_temp = 0;

/* STEPPER PINOUT
MA -> Upper stepper side A
MB -> Lower stepper side A
*/
const int PIN_MA_STEP = 0;
const int PIN_MB_STEP = 0;
const int PIN_MC_STEP = 0;
const int PIN_MD_STEP = 0;
const int PIN_MA_DIR = 0;
const int PIN_MB_DIR = 0;
const int PIN_MC_DIR = 0;
const int PIN_MD_DIR = 0;

/* LIMIT SWITCH PINOUT
m/M -> min/max
A/B -> side A or B*/
const int PIN_LSW_MXA = 0;
const int PIN_LSW_MYA = 0;
const int PIN_LSW_mXA = 0;
const int PIN_LSW_mYA = 0;
const int PIN_LSW_MXB = 0;
const int PIN_LSW_MYB = 0;
const int PIN_LSW_mXB = 0;
const int PIN_LSW_mYB = 0;

// PINOUT END ------------------------------------------------------- PINOUT END

// cut speed related variables
const unsigned int STEPPER_HIGH_DELAY = 5000;
const unsigned int STEPPER_LOW_DELAY = 5000;
unsigned int variable_high_delay = 10;
unsigned int variable_low_delay = 10;

// stepper_instruction { MA, MB, MC, MD }
int stepper_instruction[4] = { 0, 0, 0, 0 };
int machine_position[4] = { 0, 0, 0, 0 };
//------------------------------------------------------------------------------
void MoveStepper()
{
  int ax = stepper_instruction[0];
  int ay = stepper_instruction[1];
  int bx = stepper_instruction[2];
  int by = stepper_instruction[3];
  // update machine_position
  machine_position[0] = machine_position[0] + ax;
  machine_position[1] = machine_position[1] + ay;
  machine_position[2] = machine_position[2] + bx;
  machine_position[3] = machine_position[3] + by;
  // execute stepper movement
  static int MA_steps;
  static int MB_steps;
  static int MC_steps;
  static int MD_steps;
  /*
  Motion equations for coreXY
  DX = 0.5( DA + DB )
  DY = 0.5( DA - DB )
  DA = DX + DY
  DB = DX - DY
  */
  // workplane A
  MA_steps = ax + ay;
  MB_steps = ax - ay;
  // workplane B
  MC_steps = bx + by;
  MD_steps = bx - by;
  // rotation direction:
  digitalWrite( PIN_MA_DIR, LOW );
  digitalWrite( PIN_MB_DIR, LOW );
  digitalWrite( PIN_MC_DIR, LOW );
  digitalWrite( PIN_MD_DIR, LOW );
  // reverse motor direction if NXY_steps is negative
  if( MA_steps < 0 )  digitalWrite( PIN_MA_DIR, HIGH );
  if( MB_steps < 0 )  digitalWrite( PIN_MB_DIR, HIGH );
  if( MC_steps < 0 )  digitalWrite( PIN_MC_DIR, HIGH );
  if( MD_steps < 0 )  digitalWrite( PIN_MD_DIR, HIGH );
  // step pulse _-_
  if( MA_steps != 0 ) digitalWrite( PIN_MA_STEP, HIGH );
  if( MB_steps != 0 ) digitalWrite( PIN_MB_STEP, HIGH );
  if( MC_steps != 0 ) digitalWrite( PIN_MC_STEP, HIGH );
  if( MD_steps != 0 ) digitalWrite( PIN_MD_STEP, HIGH );
  // delay
  delayMicroseconds( variable_high_delay );
  // set to low
  digitalWrite( PIN_MA_STEP, LOW );
  digitalWrite( PIN_MB_STEP, LOW );
  digitalWrite( PIN_MC_STEP, LOW );
  digitalWrite( PIN_MD_STEP, LOW );
  delayMicroseconds( variable_low_delay );
  // check for double steps
  MA_steps = MA_steps / 2;
  MB_steps = MB_steps / 2;
  MC_steps = MC_steps / 2;
  MD_steps = MD_steps / 2;
  // signal out
  // step signal
  if( MA_steps != 0 ) digitalWrite( PIN_MA_STEP, HIGH );
  if( MB_steps != 0 ) digitalWrite( PIN_MB_STEP, HIGH );
  if( MC_steps != 0 ) digitalWrite( PIN_MC_STEP, HIGH );
  if( MD_steps != 0 ) digitalWrite( PIN_MD_STEP, HIGH );
  // delay
  delayMicroseconds( variable_high_delay );
  // set to low
  digitalWrite( PIN_MA_STEP, LOW );
  digitalWrite( PIN_MB_STEP, LOW );
  digitalWrite( PIN_MC_STEP, LOW );
  digitalWrite( PIN_MD_STEP, LOW );
  // end delay
  delayMicroseconds( variable_low_delay );
}
//------------------------------------------------------------------------------
void PathABCD( int Adx, int Ady, int Bdx, int Bdy )
{
  // Trajectory planning
  int delta[4] = { Adx, Ady, Bdx, Bdy };
  // determine the axis with longest travel
  int aux = 0;
  for( int i = 0; i < 4; i++ )
  {
    if( abs(delta[i]) > aux )
    {
      aux = abs(delta[i]);
    }
  }
  // calculate step ratio referenced to the longest travel
  float R[4] = { 0, 0, 0, 0 };
  for( int i = 0; i < 4; i++ )
  {
    R[i] = (float)delta[i] / (float)aux;
  }
  // iterate over the longest travel
  int inc[4] = { 0, 0, 0, 0 };
  int acc[4] = { 0, 0, 0, 0 };
  for( int j = 1; j < aux+1; j++ )
  {
    // create step instruction
    for( int i = 0; i < 4; i++ )
    {
      inc[i] = round( R[i]*j - acc[i] );
      acc[i] = acc[i] + inc[i];
      stepper_instruction[i] = inc[i];
    }
    // execute step
    MoveStepper();
    // erase step instruction array
    for( int i = 0; i < 4; i++ )
    {
      stepper_instruction[i] = 0;
    }
    Serial.println();
  }
}

void setup()
{
  Serial.begin(115200);
}

String complete_instruction[6];  // contains the decoded instruction
bool INIT = false;
void loop()
{
  while(!Serial.available()) {}  // if there is nothing on serial, do nothing
  int  i = 0;
  char raw_instruction[25];
  if(Serial.available())
  {  // if something comes from serial, read it and store it in raw_instruction char array
    delay(10); // delay to allow buffer to fill
    while(Serial.available() > 0)
    {
      raw_instruction[i] = Serial.read();
      i++;
    }
  }
  if( strlen( raw_instruction ) > 0 )  // if a new raw_instruction has been read
  {
    // clean raw_instruction before decoding (overwrite non filled array positions with empty spaces)
    for( int n = i; n < 25; n++ ) { raw_instruction[n] = ' '; }
    // decode the instruction (4 fields) (iterator n = field, iterator j = character)
    int j = 0;
    for( int n = 0; n < 5; n++ )
    {
      while( j < 25 )
      {
        if( raw_instruction[j] == ' ' )
        {
          j++;
          break;
        }
        else
        {
          complete_instruction[n] += raw_instruction[j];
        }
        j++;
      }
    }
    // print decoded instruction by serial
    if( complete_instruction[0] == "INIT" )
    {
      INIT = true; // start reading program
      Serial.println( 0 );
    }
    if( INIT == true )
    {
      if( complete_instruction[0] == "POWER" )
      {
        if( complete_instruction[1] == "ON" )
        {
         digitalWrite( PIN_PSU_POWER, LOW );
         Serial.println( 0 );
        }
        else
        {
          digitalWrite( PIN_PSU_POWER, HIGH );
          Serial.println( 0 );
        }
      }
      if( complete_instruction[0] == "WIRE" )
      {
        wire_temp = complete_instruction[1].toInt();
        analogWrite( PIN_WIRE, wire_temp );
        /*
        Serial.print( "Wire temperature set to: " );
        Serial.println( wire_temp );
        Serial.println( "DONE" );
        */
      }
      if( complete_instruction[0] == "MOVE" )
      {
        int stepsMA = round( complete_instruction[1].toFloat()*scaleMA );
        int stepsMB = round( complete_instruction[2].toFloat()*scaleMB );
        int stepsMC = round( complete_instruction[3].toFloat()*scaleMC );
        int stepsMD = round( complete_instruction[4].toFloat()*scaleMD );
        PathABCD( stepsMA, stepsMB, stepsMC, stepsMD );
        Serial.println( 0 );
      }
      if( complete_instruction[0] == "END" )
      {
        INIT = false;
        Serial.println( 0 );
      }
    }
    // erase complete_instruction array
    for( int i = 0; i < 5; i++ )
    {
      complete_instruction[i] = "";
    }
  }
}
