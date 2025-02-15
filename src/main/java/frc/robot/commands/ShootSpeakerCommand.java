// Copyright (c) FIRST and other WPILib contributors.
// Open Source Software; you can modify and/or share it under the terms of
// the WPILib BSD license file in the root directory of this project.

package frc.robot.commands;

import edu.wpi.first.wpilibj2.command.Command;
import frc.robot.subsystems.AxleSubsystem;
import frc.robot.subsystems.IntakeSubsystem;
import frc.robot.subsystems.ShooterSubsystem;

public class ShootSpeakerCommand extends Command {
  /** Creates a new ShootSpeakerCommand. */
  private final ShooterSubsystem m_Shooter;

  private final IntakeSubsystem m_Intake;
  private final AxleSubsystem m_Axle;

  public ShootSpeakerCommand(
      ShooterSubsystem sh_Subsystem, AxleSubsystem a_Subsystem, IntakeSubsystem i_Subsystem) {
    // Use addRequirements() here to declare subsystem dependencies.

    m_Shooter = sh_Subsystem;
    m_Axle = a_Subsystem;
    m_Intake = i_Subsystem;

    addRequirements(sh_Subsystem);
    addRequirements(a_Subsystem);
  }

  // Called when the command is initially scheduled.
  @Override
  public void initialize() {}

  // Called every time the scheduler runs while the command is scheduled.
  @Override
  public void execute() {
    // m_Axle.AimSpeakerAngle();
    m_Shooter.ShootSpeaker();
  }

  // Called once the command ends or is interrupted.
  @Override
  public void end(boolean interrupted) {
    if (interrupted == true) {
      m_Shooter.StopShoot();
    }
  }

  // Returns true when the command should end.
  @Override
  public boolean isFinished() {
    if (m_Intake.intakeSensor.get() == false) {
      return true;
    }
    return false;
  }
}
